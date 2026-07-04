import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import requests
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Header
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.geocoding import GeocodingService
from src.services.vedastro_service import VedAstroService, format_datetime_for_vedastro
from src.services.llm_router import LLMRouter
from src.services.pdf_service import PDFService
from src.utils.divisional_charts import map_placements_to_signs, map_divisional_signs
from src.utils.markdown_parser import strip_thinking_tags
from src.services.supabase_service import SupabaseService
from src.services.payment_service import PaymentService
from src.services.email_service import EmailService

from src.prompts.individual_report_prompts import (
    GLOBAL_SYSTEM_INSTRUCTION,
    PAGE_PROMPTS,
    USER_PROMPT_TEMPLATE,
)

app = FastAPI(title="🔮 Cosmic Report Compiler & E-Commerce Server")

# Configure CORS for Vercel / Cloudflare local and production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Mount Static Files
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

@app.get("/")
def get_root_page(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()
    is_mobile = any(x in user_agent for x in ["iphone", "android", "blackberry", "opera mini", "mobile"])
    if is_mobile:
        return FileResponse(os.path.join(static_dir, "mobile.html"))
    return FileResponse(os.path.join(static_dir, "order.html"))

@app.get("/order")
def get_order_page(request: Request):
    user_agent = request.headers.get("user-agent", "").lower()
    is_mobile = any(x in user_agent for x in ["iphone", "android", "blackberry", "opera mini", "mobile"])
    if is_mobile:
        return FileResponse(os.path.join(static_dir, "mobile.html"))
    return FileResponse(os.path.join(static_dir, "order.html"))

@app.get("/testbed")
def get_testbed_page():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, headers={"Cache-Control": "no-store, no-cache"})
    return JSONResponse(status_code=404, content={"detail": "index.html not found"})

@app.get("/success")
def get_success_page():
    return FileResponse(os.path.join(static_dir, "success.html"))

@app.get("/Coverpage.png")
def get_cover_png():
    return FileResponse(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Coverpage.png"))

@app.get("/savvy_singh.jpg")
def get_savvy_singh_jpg():
    return FileResponse(os.path.join(static_dir, "savvy_singh.jpg"))


@app.get("/admin")
def get_admin_page():
    return FileResponse(os.path.join(static_dir, "admin.html"))

@app.get("/admin/login")
def get_admin_login_page():
    return FileResponse(os.path.join(static_dir, "admin_login.html"))

@app.get("/api/config")
def get_public_config():
    return {
        "supabase_url": os.getenv("SUPABASE_URL", ""),
        "supabase_anon_key": os.getenv("SUPABASE_ANON_KEY", "")
    }


# --- Admin Authentication Dependency ---
async def get_current_admin(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization.split(" ")[1]
    
    supabase_service = SupabaseService()
    user = supabase_service.verify_admin_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized admin session")
    return user


# --- Background Worker for PDF Generation ---
async def generate_report_background_task(order_id: str, provider: str, model: str):
    """
    Executes the heavy VedAstro API calculations, LLM router synthesis,
    Playwright PDF rendering, and uploads to Supabase Storage in the background.
    """
    supabase = SupabaseService()
    email_service = EmailService()
    
    print(f"[BackgroundTask] Starting report generation for Order {order_id}...")
    supabase.update_order_status(order_id, "processing", "generating")
    
    order = supabase.get_order_by_id(order_id)
    if not order:
        print(f"[BackgroundTask] Order {order_id} not found.")
        return
        
    cust = order.get("customers") or {}
    
    try:
        lat = order["latitude"]
        lon = order["longitude"]
        tz = order["timezone"]
        dob = str(order["dob"])
        tob = str(order["tob"])
        place = order["place"]
        name = cust.get("full_name", "User")
        gender = order.get("geocoded_place", {}).get("gender", "Female") # default gender parsed during order creation
        
        # Format datetime for VedAstro calculations
        dt_str = f"{dob}T{tob}"
        time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, tz)
        
        vedastro = VedAstroService()
        
        # Load D1 placements and divisional metrics
        d1_data = vedastro.get_all_planet_data(place, lat, lon, time_str, date_str, offset_str)
        house_signs = vedastro.get_all_house_rasi_signs(lat, lon, time_str, date_str, offset_str)
        d9_signs = vedastro.get_all_planet_navamsha_signs(lat, lon, time_str, date_str, offset_str)
        d30_signs = vedastro.get_all_planet_trimshamsha_signs(lat, lon, time_str, date_str, offset_str)
        
        lagna_sign = vedastro.get_lagna_sign_name(lat, lon, time_str, date_str, offset_str)
        lagna_tags = vedastro.get_sign_tags(lagna_sign)
        lagna_lord = vedastro.get_lord_of_house("House1", lat, lon, time_str, date_str, offset_str)
        house5_lord = vedastro.get_lord_of_house("House5", lat, lon, time_str, date_str, offset_str)
        house7_lord = vedastro.get_lord_of_house("House7", lat, lon, time_str, date_str, offset_str)
        
        house5_sign = house_signs.get("House5", "Leo")
        house7_sign = house_signs.get("House7", "Aquarius")
        house5_planets = vedastro.get_planets_in_house("House5", lat, lon, time_str, date_str, offset_str)
        house7_planets = vedastro.get_planets_in_house("House7", lat, lon, time_str, date_str, offset_str)
        
        venus_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Leo") for entry in d1_data for p, d in entry.items() if p == "Venus"), "Leo")
        venus_conjunctions = vedastro.get_planets_in_conjunction("Venus", lat, lon, time_str, date_str, offset_str)
        is_venus_combust = "Yes" if vedastro.is_planet_combust_specific("Venus", lat, lon, time_str, date_str, offset_str) else "No"
        
        venus_relationships = []
        for conj in venus_conjunctions:
            rel = vedastro.get_planet_relationship("Venus", conj, lat, lon, time_str, date_str, offset_str)
            venus_relationships.append(f"{conj} ({rel})")
            
        navamsa_lagna_sign = house_signs.get("House1", "Virgo")
        try:
            navamsa_lagna_sign = vedastro.get_house_navamsha_d9_sign("House1", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        navamsa_house7_sign = "Aries"
        try:
            navamsa_house7_sign = vedastro.get_house_navamsha_d9_sign("House7", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        trimsamsha_house7_sign = "Aquarius"
        try:
            trimsamsha_house7_sign = vedastro.get_house_trimshamsha_d30_sign("House7", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        trimsamsha_lagna_sign = "Aries"
        try:
            trimsamsha_lagna_sign = vedastro.get_house_trimshamsha_d30_sign("House1", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        kuja_dosha_score = vedastro.get_kuja_dosha_score(lat, lon, time_str, date_str, offset_str)
        is_7th_lord_afflicted = "Yes" if vedastro.is_planet_afflicted_specific(house7_lord, lat, lon, time_str, date_str, offset_str) else "No"
        
        afflicted_planets = []
        for entry in d1_data:
            for p, d in entry.items():
                if d.get("IsPlanetAfflicted") == "True":
                    afflicted_planets.append(p)
                    
        malefic_planets = vedastro.get_malefic_planet_list(lat, lon, time_str, date_str, offset_str)
        benefic_planets = vedastro.get_benefic_planet_list(lat, lon, time_str, date_str, offset_str)
        
        dasa_now_raw = vedastro.get_dasa_for_now(lat, lon, time_str, date_str, offset_str, levels=3)
        dasa_now = f"{dasa_now_raw.get('Major', '')} - {dasa_now_raw.get('Sub', '')} - {dasa_now_raw.get('SubSub', '')}"
        
        dasa_info_for_asc = vedastro.get_dasa_info_for_ascendant(lagna_sign)
        
        # Calculate Dasha timeline
        now = datetime.now()
        three_years_later = now + timedelta(days=3 * 365)
        start_t, start_d, _ = format_datetime_for_vedastro(now.isoformat(), tz)
        end_t, end_d, _ = format_datetime_for_vedastro(three_years_later.isoformat(), tz)
        
        dasa_timeline_raw = []
        try:
            dasa_timeline_raw = vedastro.get_dasa_at_range(
                lat, lon, time_str, date_str, offset_str,
                start_t, start_d, end_t, end_d, levels=2, precision_hours=48
            )
        except Exception:
            pass
            
        d1_placements = map_placements_to_signs(d1_data)
        d9_placements = map_divisional_signs(d9_signs)
        d30_placements = map_divisional_signs(d30_signs)
        
        # Elements
        elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        fire_signs = ["Aries", "Leo", "Sagittarius"]
        earth_signs = ["Taurus", "Virgo", "Capricorn"]
        air_signs = ["Gemini", "Libra", "Aquarius"]
        water_signs = ["Cancer", "Scorpio", "Pisces"]
        for sign, planets in d1_placements.items():
            if sign in fire_signs:
                elements["Fire"] += len(planets)
            elif sign in earth_signs:
                elements["Earth"] += len(planets)
            elif sign in air_signs:
                elements["Air"] += len(planets)
            elif sign in water_signs:
                elements["Water"] += len(planets)
                
        # Risk Matrix
        risk_matrix = []
        for aff_planet in afflicted_planets[:3]:
            tags = vedastro.get_planet_tags(aff_planet)
            risk_matrix.append([
                f"Afflicted {aff_planet}",
                f"Causes shadows of {tags.split(',')[0] if tags else 'emotional blocks'}.",
                f"Conscious focus on releasing control and seeking stability."
            ])
        if kuja_dosha_score > 0:
            risk_matrix.append([
                f"Kuja Dosha ({int(kuja_dosha_score)}%)",
                "Triggers defensive blocks, stubbornness, or hot-headed responses.",
                "Practice cooling breathwork and wait 24 hours before responding to conflicts."
            ])
        if not risk_matrix:
            risk_matrix.append(["General Balance", "Minor friction points in communication.", "Commit to open dialogue."])
            
        # Dasha Forecast
        dasha_timeline = []
        if not dasa_timeline_raw:
            dasha_timeline.append([dasa_now.split("-")[0], f"{dob} to Future", "Major cycle guiding long term spiritual growth."])
        else:
            for item in dasa_timeline_raw[:4]:
                dasha_timeline.append([
                    item.get("Name", "Unknown Dasa"),
                    f"{item.get('StartTime', {}).get('Readable', '')[:11]} - {item.get('EndTime', {}).get('Readable', '')[:11]}",
                    "Favorable window for emotional breakthroughs and setting roots."
                ])
                
        # Formatting variables
        lagna_tags_str = lagna_tags if lagna_tags else "expressive, initiating"
        moon_nakshatra = next((d.get("PlanetConstellation", "Chitta") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Chitta")
        moon_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Libra") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Libra")
        moon_tags = vedastro.get_sign_tags(moon_sign)
        house7_tags = vedastro.get_house_tags("House7")
        planet_navamsa_signs_str = ", ".join([f"{p}: {s}" for p, s in d9_signs.items()])
        planet_trimsamsha_signs_str = ", ".join([f"{p}: {s}" for p, s in d30_signs.items()])
        dasa_timeline_str = ", ".join([f"{row[0]} ({row[1]})" for row in dasha_timeline])
        
        remedies_data_str = ""
        for p in afflicted_planets[:2]:
            p_tags = vedastro.get_planet_tags(p)
            remedies_data_str += f"{p} (afflicted, tags: {p_tags}); "
            
        favorable_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in benefic_planets[:2]])
        afflicted_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in malefic_planets[:2]])
        dasa_info_str = str(dasa_info_for_asc.get("Description", "Growth and commitment dasha rules."))
        
        router = LLMRouter()
        sections_text = {}
        pages_to_generate = [p for p in PAGE_PROMPTS.keys()]
        
        # Sequential LLM calls with pacing
        for page in pages_to_generate:
            instruction = PAGE_PROMPTS[page].format(
                lagna_sign=lagna_sign, lagna_lord=lagna_lord, lagna_tags=lagna_tags_str,
                moon_sign=moon_sign, moon_nakshatra=moon_nakshatra, moon_tags=moon_tags,
                house5_sign=house5_sign, house5_lord=house5_lord,
                house5_planets=", ".join(house5_planets) if house5_planets else "None",
                venus_sign=venus_sign,
                venus_conjunctions=", ".join(venus_conjunctions) if venus_conjunctions else "None",
                is_venus_combust=is_venus_combust,
                venus_relationships=", ".join(venus_relationships) if venus_relationships else "None",
                house7_sign=house7_sign, house7_lord=house7_lord,
                house7_planets=", ".join(house7_planets) if house7_planets else "None",
                house7_tags=house7_tags,
                house7_lord_sign=next((d.get("PlanetRasiD1Sign", {}).get("Name", "Virgo") for entry in d1_data for p, d in entry.items() if p == house7_lord), "Virgo"),
                house7_lord_house=str(next((d.get("PlanetHouse", 1) for entry in d1_data for p, d in entry.items() if p == house7_lord), 1)),
                navamsa_lagna_sign=navamsa_lagna_sign, planet_navamsa_signs=planet_navamsa_signs_str,
                navamsa_house7_sign=navamsa_house7_sign, navamsa_house7_lord="Saturn", navamsa_house7_planets="None",
                trimsamsha_house7_sign=trimsamsha_house7_sign, planet_trimsamsha_signs=planet_trimsamsha_signs_str,
                afflicted_planets=", ".join(afflicted_planets) if afflicted_planets else "None",
                is_7th_lord_afflicted=is_7th_lord_afflicted, kuja_dosha_score=f"{kuja_dosha_score}%",
                mars_afflictions="retrograde" if "Mars" in afflicted_planets else "None",
                malefic_planets=", ".join(malefic_planets), benefic_planets=", ".join(benefic_planets),
                element_fire=elements["Fire"], element_earth=elements["Earth"],
                element_air=elements["Air"], element_water=elements["Water"],
                dasa_now=dasa_now, dasa_timeline=dasa_timeline_str,
                pratyantar_dasha=dasa_now_raw.get("SubSub", "Mercury"),
                favorable_tags=favorable_tags_str, afflicted_tags=afflicted_tags_str,
                remedies_data=remedies_data_str, dasa_info_for_ascendant=dasa_info_str
            )
            
            user_prompt = USER_PROMPT_TEMPLATE.format(
                page_number=page, page_instruction=instruction,
                name=name, gender=gender,
                birth_details=f"{dob} at {tob} in {place}"
            )
            
            raw_text = router.generate(
                provider=provider,
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                user_prompt=user_prompt,
                model=model
            )
            sections_text[page] = strip_thinking_tags(raw_text)
            
            # Pacing sleep
            await asyncio.sleep(2.0)
            
        # PDF compilation via PDFService
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"{order_id}_report.pdf")
        
        pdf_service = PDFService()
        pdf_service.build_pdf_report(
            output_path=pdf_path,
            sections=sections_text,
            d1_placements=d1_placements,
            d9_placements=d9_placements,
            d30_placements=d30_placements,
            risk_matrix=risk_matrix,
            dasha_timeline=dasha_timeline,
            client_name=name,
            birth_details=f"{dob} at {tob} in {place}",
            lagna_sign=lagna_sign,
            navamsa_lagna_sign=navamsa_lagna_sign,
            trimsamsha_lagna_sign=trimsamsha_lagna_sign,
            client_dob=dob,
            client_tob=tob,
            client_pob=place,
        )
        
        # Upload generated report PDF to Supabase Storage
        report_url = supabase.upload_pdf_report(order_id, pdf_path)
        if report_url:
            supabase.update_order_report(order_id, report_url)
            print(f"[BackgroundTask] Completed generation for Order {order_id} at {report_url}")
        else:
            raise RuntimeError("Report upload to Supabase Storage failed.")
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        supabase.update_order_status(order_id, "failed", "failed")
        print(f"[BackgroundTask] PDF compilation failed for Order {order_id}: {e}")


# --- Public E-Commerce APIs ---

@app.get("/api/geocode")
def api_geocode(q: str):
    """Proxy autocomplete search directly using VedAstro AddressToGeoLocation API."""
    if not q or not q.strip():
        return {"results": []}
        
    url = f"https://api.vedastro.org/api/Calculate/AddressToGeoLocation/Address/{q}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("Status") == "Pass":
            loc = data["Payload"]["AddressToGeoLocation"]
            # Fetch timezone coordinates via OpenCage mapping for accuracy
            opencage_key = os.getenv("OPENCAGE_API_KEY", "3723e0d7ceb64eb3bd3623477d4c3142")
            geocoder = GeocodingService(opencage_key)
            geo_info = geocoder.geocode(loc["Name"])
            tz = geo_info["timezone"] if geo_info else "Asia/Kolkata"
            
            return {
                "results": [{
                    "formatted": loc["Name"],
                    "latitude": loc["Latitude"],
                    "longitude": loc["Longitude"],
                    "timezone": tz,
                    "raw": loc
                }]
            }
        return {"results": []}
    except Exception as e:
        print(f"[GeocodeProxy] Error: {e}")
        return {"results": []}


class CreateOrderRequest(BaseModel):
    name: str
    email: str
    mobile: str
    gender: str
    dob: str
    tob: str
    place: str
    latitude: float
    longitude: float
    timezone: str
    geocoded_place: Dict[str, Any]

@app.post("/api/orders/create")
async def api_create_order(req: CreateOrderRequest):
    """Register customer, record order in Supabase, and spawn Razorpay Order ID."""
    supabase = SupabaseService()
    payment_service = PaymentService()
    
    try:
        # 1. Customer signup / resolve
        customer_id = supabase.get_or_create_customer(req.name, req.email, req.mobile)
        
        # 2. Append gender to geocoded metadata
        geo_payload = req.geocoded_place.copy()
        geo_payload["gender"] = req.gender
        
        # 3. Save pending order details
        order_id = supabase.create_order(
            customer_id=customer_id,
            dob=req.dob,
            tob=req.tob,
            place=req.place,
            lat=req.latitude,
            lng=req.longitude,
            tz=req.timezone,
            geocoded_place=geo_payload
        )
        
        # 4. Generate Razorpay Order
        rz_order = payment_service.create_razorpay_order(499.00, order_id)
        supabase.create_payment(order_id, rz_order["id"], 499.00)
        
        return {
            "order_id": order_id,
            "razorpay_order_id": rz_order["id"],
            "amount": rz_order["amount"],
            "currency": "INR"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class VerifyPaymentRequest(BaseModel):
    order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@app.post("/api/payments/verify")
async def api_verify_payment(req: VerifyPaymentRequest, background_tasks: BackgroundTasks):
    """Verifies Razorpay payment signature, captures order, triggers email, spawns background report generation."""
    supabase = SupabaseService()
    payment_service = PaymentService()
    email_service = EmailService()
    
    # 1. Verify Signature
    verified = payment_service.verify_payment_signature(
        req.razorpay_order_id,
        req.razorpay_payment_id,
        req.razorpay_signature
    )
    if not verified:
        supabase.update_order_status(req.order_id, "failed")
        raise HTTPException(status_code=400, detail="Razorpay signature verification failed.")
        
    try:
        # 2. Confirm Payment details & capture
        supabase.confirm_payment(req.razorpay_order_id, req.razorpay_payment_id, req.model_dump())
        supabase.update_order_status(req.order_id, "paid", "not_started")
        
        order = supabase.get_order_by_id(req.order_id)
        cust = order.get("customers") or {}
        
        # 3. Fire immediate 24-36 hour confirmation email
        sent = email_service.send_order_confirmation(cust["email"], cust["full_name"], req.order_id)
        supabase.log_email(req.order_id, "order_confirmation", cust["email"], "sent" if sent else "failed")
        
        # 4. Spawn background async report generation task
        background_tasks.add_task(
            generate_report_background_task,
            order_id=req.order_id,
            provider="google",
            model="gemini-1.5-pro"
        )
        
        return {"status": "success", "detail": "Payment captured and order generation started."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Admin Dashboard APIs (JWT Protected) ---

@app.get("/api/admin/orders")
async def api_admin_orders(status: Optional[str] = None, search: Optional[str] = None, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    orders = supabase.get_orders(status, search)
    return {"orders": orders}

@app.get("/api/admin/orders/{order_id}")
async def api_admin_order_detail(order_id: str, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    logs = supabase.get_email_logs(order_id)
    return {"order": order, "email_logs": logs}

class UpdateNotesRequest(BaseModel):
    notes: str

@app.post("/api/admin/orders/{order_id}/notes")
async def api_admin_update_notes(order_id: str, req: UpdateNotesRequest, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    success = supabase.save_admin_notes(order_id, req.notes)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save admin notes")
    return {"status": "success"}

class UpdateStatusRequest(BaseModel):
    status: str

@app.post("/api/admin/orders/{order_id}/status")
async def api_admin_update_status(order_id: str, req: UpdateStatusRequest, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    success = supabase.update_order_status(order_id, req.status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update order status")
    return {"status": "success"}

@app.post("/api/admin/orders/{order_id}/generate")
async def api_admin_trigger_generate(order_id: str, background_tasks: BackgroundTasks, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    background_tasks.add_task(
        generate_report_background_task,
        order_id=order_id,
        provider="google",
        model="gemini-1.5-pro"
    )
    return {"status": "success", "detail": "Async report generation re-triggered."}

class ManualUploadRequest(BaseModel):
    report_url: str

@app.post("/api/admin/orders/{order_id}/upload")
async def api_admin_manual_upload(order_id: str, req: ManualUploadRequest, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    success = supabase.update_order_report(order_id, req.report_url)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload manual report url")
    return {"status": "success"}

@app.post("/api/admin/orders/{order_id}/resend-confirmation")
async def api_admin_resend_confirmation(order_id: str, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    email_service = EmailService()
    
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    cust = order.get("customers") or {}
    sent = email_service.send_order_confirmation(cust["email"], cust["full_name"], order_id)
    supabase.log_email(order_id, "order_confirmation", cust["email"], "sent" if sent else "failed")
    
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to resend confirmation email")
    return {"status": "success"}

@app.post("/api/admin/orders/{order_id}/send-report")
async def api_admin_send_report(order_id: str, admin: Any = Header(None)):
    await get_current_admin(admin)
    supabase = SupabaseService()
    email_service = EmailService()
    
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if not order.get("report_url"):
        raise HTTPException(status_code=400, detail="Report has not been generated yet.")
        
    cust = order.get("customers") or {}
    sent = email_service.send_report_delivered(cust["email"], cust["full_name"], order_id, order["report_url"])
    supabase.log_email(order_id, "report_delivered", cust["email"], "sent" if sent else "failed")
    
    if sent:
        supabase.update_order_status(order_id, "delivered")
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Email delivery failed")

# --- Legacy Testbed API Endpoint (For Backward Compatibility) ---
class GenerateRequest(BaseModel):
    name: str
    gender: str
    dob: str
    tob: str
    place: str
    provider: str
    model: Optional[str] = None

@app.post("/api/generate")
async def api_generate(req: GenerateRequest, session_id: str):
    """Existing direct-compile API for testing playground."""
    # Instantly returns compile output to direct playground interface
    try:
        # Geocode birth place
        opencage_key = os.getenv("OPENCAGE_API_KEY", "3723e0d7ceb64eb3bd3623477d4c3142")
        geocoder = GeocodingService(opencage_key)
        geo = geocoder.geocode(req.place)
        if not geo:
            raise ValueError(f"Could not geocode location: '{req.place}'")
        
        lat = geo["latitude"]
        lon = geo["longitude"]
        tz = geo["timezone"]
        dt_str = f"{req.dob}T{req.tob}:00"
        time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, tz)
        
        vedastro = VedAstroService()
        d1_data = vedastro.get_all_planet_data(req.place, lat, lon, time_str, date_str, offset_str)
        house_signs = vedastro.get_all_house_rasi_signs(lat, lon, time_str, date_str, offset_str)
        d9_signs = vedastro.get_all_planet_navamsha_signs(lat, lon, time_str, date_str, offset_str)
        d30_signs = vedastro.get_all_planet_trimshamsha_signs(lat, lon, time_str, date_str, offset_str)
        
        lagna_sign = vedastro.get_lagna_sign_name(lat, lon, time_str, date_str, offset_str)
        lagna_tags = vedastro.get_sign_tags(lagna_sign)
        lagna_lord = vedastro.get_lord_of_house("House1", lat, lon, time_str, date_str, offset_str)
        house5_lord = vedastro.get_lord_of_house("House5", lat, lon, time_str, date_str, offset_str)
        house7_lord = vedastro.get_lord_of_house("House7", lat, lon, time_str, date_str, offset_str)
        
        house5_sign = house_signs.get("House5", "Leo")
        house7_sign = house_signs.get("House7", "Aquarius")
        house5_planets = vedastro.get_planets_in_house("House5", lat, lon, time_str, date_str, offset_str)
        house7_planets = vedastro.get_planets_in_house("House7", lat, lon, time_str, date_str, offset_str)
        
        venus_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Leo") for entry in d1_data for p, d in entry.items() if p == "Venus"), "Leo")
        venus_conjunctions = vedastro.get_planets_in_conjunction("Venus", lat, lon, time_str, date_str, offset_str)
        is_venus_combust = "Yes" if vedastro.is_planet_combust_specific("Venus", lat, lon, time_str, date_str, offset_str) else "No"
        
        venus_relationships = []
        for conj in venus_conjunctions:
            rel = vedastro.get_planet_relationship("Venus", conj, lat, lon, time_str, date_str, offset_str)
            venus_relationships.append(f"{conj} ({rel})")
            
        navamsa_lagna_sign = house_signs.get("House1", "Virgo")
        try:
            navamsa_lagna_sign = vedastro.get_house_navamsha_d9_sign("House1", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        navamsa_house7_sign = "Aries"
        try:
            navamsa_house7_sign = vedastro.get_house_navamsha_d9_sign("House7", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        trimsamsha_house7_sign = "Aquarius"
        try:
            trimsamsha_house7_sign = vedastro.get_house_trimshamsha_d30_sign("House7", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        trimsamsha_lagna_sign = "Aries"
        try:
            trimsamsha_lagna_sign = vedastro.get_house_trimshamsha_d30_sign("House1", lat, lon, time_str, date_str, offset_str)
        except Exception:
            pass
            
        kuja_dosha_score = vedastro.get_kuja_dosha_score(lat, lon, time_str, date_str, offset_str)
        is_7th_lord_afflicted = "Yes" if vedastro.is_planet_afflicted_specific(house7_lord, lat, lon, time_str, date_str, offset_str) else "No"
        
        afflicted_planets = []
        for entry in d1_data:
            for p, d in entry.items():
                if d.get("IsPlanetAfflicted") == "True":
                    afflicted_planets.append(p)
                    
        malefic_planets = vedastro.get_malefic_planet_list(lat, lon, time_str, date_str, offset_str)
        benefic_planets = vedastro.get_benefic_planet_list(lat, lon, time_str, date_str, offset_str)
        
        dasa_now_raw = vedastro.get_dasa_for_now(lat, lon, time_str, date_str, offset_str, levels=3)
        dasa_now = f"{dasa_now_raw.get('Major', '')} - {dasa_now_raw.get('Sub', '')} - {dasa_now_raw.get('SubSub', '')}"
        
        dasa_info_for_asc = vedastro.get_dasa_info_for_ascendant(lagna_sign)
        
        now = datetime.now()
        three_years_later = now + timedelta(days=3 * 365)
        start_t, start_d, _ = format_datetime_for_vedastro(now.isoformat(), tz)
        end_t, end_d, _ = format_datetime_for_vedastro(three_years_later.isoformat(), tz)
        
        dasa_timeline_raw = []
        try:
            dasa_timeline_raw = vedastro.get_dasa_at_range(
                lat, lon, time_str, date_str, offset_str,
                start_t, start_d, end_t, end_d, levels=2, precision_hours=48
            )
        except Exception:
            pass
            
        d1_placements = map_placements_to_signs(d1_data)
        d9_placements = map_divisional_signs(d9_signs)
        d30_placements = map_divisional_signs(d30_signs)
        
        elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
        fire_signs = ["Aries", "Leo", "Sagittarius"]
        earth_signs = ["Taurus", "Virgo", "Capricorn"]
        air_signs = ["Gemini", "Libra", "Aquarius"]
        water_signs = ["Cancer", "Scorpio", "Pisces"]
        for sign, planets in d1_placements.items():
            if sign in fire_signs:
                elements["Fire"] += len(planets)
            elif sign in earth_signs:
                elements["Earth"] += len(planets)
            elif sign in air_signs:
                elements["Air"] += len(planets)
            elif sign in water_signs:
                elements["Water"] += len(planets)
                
        risk_matrix = []
        for aff_planet in afflicted_planets[:3]:
            tags = vedastro.get_planet_tags(aff_planet)
            risk_matrix.append([
                f"Afflicted {aff_planet}",
                f"Causes shadows of {tags.split(',')[0] if tags else 'emotional blocks'}.",
                f"Conscious focus on releasing control and seeking stability."
            ])
        if kuja_dosha_score > 0:
            risk_matrix.append([
                f"Kuja Dosha ({int(kuja_dosha_score)}%)",
                "Triggers defensive blocks, stubbornness, or hot-headed responses.",
                "Practice cooling breathwork and wait 24 hours before responding to conflicts."
            ])
        if not risk_matrix:
            risk_matrix.append(["General Balance", "Minor friction points in communication.", "Commit to open dialogue."])
            
        dasha_timeline = []
        if not dasa_timeline_raw:
            dasha_timeline.append([dasa_now.split("-")[0], f"{req.dob} to Future", "Major cycle guiding long term spiritual growth."])
        else:
            for item in dasa_timeline_raw[:4]:
                dasha_timeline.append([
                    item.get("Name", "Unknown Dasa"),
                    f"{item.get('StartTime', {}).get('Readable', '')[:11]} - {item.get('EndTime', {}).get('Readable', '')[:11]}",
                    "Favorable window for emotional breakthroughs and setting roots."
                ])
                
        lagna_tags_str = lagna_tags if lagna_tags else "expressive, initiating"
        moon_nakshatra = next((d.get("PlanetConstellation", "Chitta") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Chitta")
        moon_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Libra") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Libra")
        moon_tags = vedastro.get_sign_tags(moon_sign)
        house7_tags = vedastro.get_house_tags("House7")
        planet_navamsa_signs_str = ", ".join([f"{p}: {s}" for p, s in d9_signs.items()])
        planet_trimsamsha_signs_str = ", ".join([f"{p}: {s}" for p, s in d30_signs.items()])
        dasa_timeline_str = ", ".join([f"{row[0]} ({row[1]})" for row in dasha_timeline])
        
        remedies_data_str = ""
        for p in afflicted_planets[:2]:
            p_tags = vedastro.get_planet_tags(p)
            remedies_data_str += f"{p} (afflicted, tags: {p_tags}); "
            
        favorable_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in benefic_planets[:2]])
        afflicted_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in malefic_planets[:2]])
        dasa_info_str = str(dasa_info_for_asc.get("Description", "Growth and commitment dasha rules."))
        
        router = LLMRouter()
        sections_text = {}
        pages_to_generate = [p for p in PAGE_PROMPTS.keys()]
        
        for idx, page in enumerate(pages_to_generate):
            instruction = PAGE_PROMPTS[page].format(
                lagna_sign=lagna_sign, lagna_lord=lagna_lord, lagna_tags=lagna_tags_str,
                moon_sign=moon_sign, moon_nakshatra=moon_nakshatra, moon_tags=moon_tags,
                house5_sign=house5_sign, house5_lord=house5_lord,
                house5_planets=", ".join(house5_planets) if house5_planets else "None",
                venus_sign=venus_sign,
                venus_conjunctions=", ".join(venus_conjunctions) if venus_conjunctions else "None",
                is_venus_combust=is_venus_combust,
                venus_relationships=", ".join(venus_relationships) if venus_relationships else "None",
                house7_sign=house7_sign, house7_lord=house7_lord,
                house7_planets=", ".join(house7_planets) if house7_planets else "None",
                house7_tags=house7_tags,
                house7_lord_sign=next((d.get("PlanetRasiD1Sign", {}).get("Name", "Virgo") for entry in d1_data for p, d in entry.items() if p == house7_lord), "Virgo"),
                house7_lord_house=str(next((d.get("PlanetHouse", 1) for entry in d1_data for p, d in entry.items() if p == house7_lord), 1)),
                navamsa_lagna_sign=navamsa_lagna_sign, planet_navamsa_signs=planet_navamsa_signs_str,
                navamsa_house7_sign=navamsa_house7_sign, navamsa_house7_lord="Saturn", navamsa_house7_planets="None",
                trimsamsha_house7_sign=trimsamsha_house7_sign, planet_trimsamsha_signs=planet_trimsamsha_signs_str,
                afflicted_planets=", ".join(afflicted_planets) if afflicted_planets else "None",
                is_7th_lord_afflicted=is_7th_lord_afflicted, kuja_dosha_score=f"{kuja_dosha_score}%",
                mars_afflictions="retrograde" if "Mars" in afflicted_planets else "None",
                malefic_planets=", ".join(malefic_planets), benefic_planets=", ".join(benefic_planets),
                element_fire=elements["Fire"], element_earth=elements["Earth"],
                element_air=elements["Air"], element_water=elements["Water"],
                dasa_now=dasa_now, dasa_timeline=dasa_timeline_str,
                pratyantar_dasha=dasa_now_raw.get("SubSub", "Mercury"),
                favorable_tags=favorable_tags_str, afflicted_tags=afflicted_tags_str,
                remedies_data=remedies_data_str, dasa_info_for_ascendant=dasa_info_str
            )
            
            user_prompt = USER_PROMPT_TEMPLATE.format(
                page_number=page, page_instruction=instruction,
                name=req.name, gender=req.gender,
                birth_details=f"{req.dob} at {req.tob} in {req.place}"
            )
            
            raw_text = router.generate(
                provider=req.provider,
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                user_prompt=user_prompt,
                model=req.model
            )
            sections_text[page] = strip_thinking_tags(raw_text)
            
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        pdf_path = os.path.join(output_dir, f"{session_id}_report.pdf")
        
        pdf_service = PDFService()
        pdf_service.build_pdf_report(
            output_path=pdf_path,
            sections=sections_text,
            d1_placements=d1_placements,
            d9_placements=d9_placements,
            d30_placements=d30_placements,
            risk_matrix=risk_matrix,
            dasha_timeline=dasha_timeline,
            client_name=req.name,
            birth_details=f"{req.dob} at {req.tob} in {req.place}",
            lagna_sign=lagna_sign,
            navamsa_lagna_sign=navamsa_lagna_sign,
            trimsamsha_lagna_sign=trimsamsha_lagna_sign,
            client_dob=req.dob,
            client_tob=req.tob,
            client_pob=req.place,
        )
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{req.name.lower()}_individual_love_report.pdf")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
