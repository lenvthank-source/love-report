import os
import sys
import time
import json
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import requests
from pydantic import BaseModel

# Business rules: Auto-deliver reports after +4 hours of "window time"
# Window time is daily from 11:00 AM to 7:00 PM India Standard Time (IST)
def calculate_delivery_time_ist(order_time_utc: datetime) -> datetime:
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    current_ist = order_time_utc.astimezone(ist_tz)
    
    remaining_delay_minutes = 240 # 4 hours
    
    while remaining_delay_minutes > 0:
        window_start = current_ist.replace(hour=11, minute=0, second=0, microsecond=0)
        window_end = current_ist.replace(hour=19, minute=0, second=0, microsecond=0)
        
        if current_ist < window_start:
            current_ist = window_start
        elif current_ist >= window_end:
            next_day = current_ist + timedelta(days=1)
            current_ist = next_day.replace(hour=11, minute=0, second=0, microsecond=0)
        else:
            minutes_left_in_window = int((window_end - current_ist).total_seconds() / 60)
            if remaining_delay_minutes <= minutes_left_in_window:
                current_ist = current_ist + timedelta(minutes=remaining_delay_minutes)
                remaining_delay_minutes = 0
            else:
                remaining_delay_minutes -= minutes_left_in_window
                next_day = current_ist + timedelta(days=1)
                current_ist = next_day.replace(hour=11, minute=0, second=0, microsecond=0)
                
    return current_ist.astimezone(timezone.utc)

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Header
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
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
from validate_pdf_report import validate_pdf
from src.cache.file_cache import FileCache
from opencage.geocoder import OpenCageGeocode


from src.prompts.individual_report_prompts import (
    GLOBAL_SYSTEM_INSTRUCTION,
    PAGE_PROMPTS,
    USER_PROMPT_TEMPLATE,
    PAGE_WORD_LIMITS,
)

def get_rudraksha_remedy(gender: str, moon_sign: str, sun_sign: str) -> str:
    # Sign maps
    moon_map = {
        "Aries": "1 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/1-mukhi-rudraksha-nepali",
        "Taurus": "6 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/6-mukhi-rudraksha-nepali",
        "Gemini": "4 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/4-mukhi-rudraksha-nepali",
        "Cancer": "2 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/2-mukhi-rudraksha-nepali",
        "Leo": "1 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/1-mukhi-rudraksha-nepali",
        "Virgo": "10 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/10-mukhi-rudraksha-nepali",
        "Libra": "7 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/7-mukhi-rudraksha-nepali",
        "Scorpio": "3 mukhi Rudraksha (Indian) - https://www.astrosavvysingh.com/product/3-mukhi-rudraksha-indian",
        "Sagittarius": "5 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/5-mukhi-rudraksha-nepali",
        "Capricorn": "14 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/14-mukhi-rudraksha-nepali",
        "Aquarius": "7 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/7-mukhi-rudraksha-nepali",
        "Pisces": "2 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/2-mukhi-rudraksha-nepali"
    }
    
    sun_map = {
        "Aries": "3 mukhi Rudraksha (Indian) - https://www.astrosavvysingh.com/product/3-mukhi-rudraksha-indian",
        "Taurus": "13 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/13-mukhi-rudraksha-nepali",
        "Gemini": "5 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/5-mukhi-rudraksha-nepali",
        "Cancer": "1 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/1-mukhi-rudraksha-nepali",
        "Leo": "12 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/12-mukhi-rudraksha-nepali",
        "Virgo": "4 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/4-mukhi-rudraksha-nepali",
        "Libra": "6 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/6-mukhi-rudraksha-nepali",
        "Scorpio": "8 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/8-mukhi-rudraksha-nepali",
        "Sagittarius": "10 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/10-mukhi-rudraksha-nepali",
        "Capricorn": "7 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/7-mukhi-rudraksha-nepali",
        "Aquarius": "9 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/9-mukhi-rudraksha-nepali",
        "Pisces": "5 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/5-mukhi-rudraksha-nepali"
    }
    
    # Normalize sign names to match keys (capitalize first letter, strip spaces)
    m_sign = str(moon_sign).strip().capitalize()
    s_sign = str(sun_sign).strip().capitalize()
    g = str(gender).strip().lower()
    
    if "female" in g:
        return moon_map.get(m_sign, "7 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/7-mukhi-rudraksha-nepali")
    else:
        return sun_map.get(s_sign, "5 mukhi Rudraksha (Nepali) - https://www.astrosavvysingh.com/product/5-mukhi-rudraksha-nepali")

app = FastAPI(title="🔮 Cosmic Report Compiler & E-Commerce Server")

# Global Caches for Geocoding Autocomplete
geocode_file_cache = FileCache(cache_dir="cache_geocode")
geocode_mem_cache = {}

# Global Geocoder Client
opencage_key_val = os.getenv("OPENCAGE_API_KEY", "3723e0d7ceb64eb3bd3623477d4c3142")
geocoder_client = OpenCageGeocode(opencage_key_val)


# Configure CORS for Vercel / Cloudflare local and production domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Mount Static Files
static_dir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
)

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
    success_path = os.path.join(static_dir, "success.html")
    if not os.path.exists(success_path):
        return HTMLResponse("success.html not found", status_code=404)
        
    try:
        with open(success_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        pixel_id = os.getenv("META_PIXEL_ID", "")
        # Dynamically inject META_PIXEL_ID into success page
        content = content.replace("<!-- META_PIXEL_ID -->", pixel_id)
        
        return HTMLResponse(content)
    except Exception as e:
        print(f"[SuccessPage] Error loading template: {e}")
        return HTMLResponse("Error loading order confirmation page.", status_code=500)

@app.get("/love-calculator")
def get_love_calculator():
    return FileResponse(os.path.join(static_dir, "love_calculator.html"))


@app.get("/Coverpage.png")
def get_cover_png():
    return FileResponse(os.path.join(static_dir, "Coverpage.png"))

@app.get("/savvy_singh.jpg")
def get_savvy_singh_jpg():
    return FileResponse(os.path.join(static_dir, "savvy_singh.jpg"))

@app.get("/favicon.png")
def get_favicon_png():
    return FileResponse(os.path.join(static_dir, "favicon.png"))

@app.get("/favicon.ico")
def get_favicon_ico():
    return FileResponse(os.path.join(static_dir, "favicon.ico"))



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


@app.get("/api/health")
def api_health():
    """System health check endpoint verifying database connectivity and configuration status."""
    supabase = SupabaseService()
    db_connected = supabase.check_connection()
    
    payment = PaymentService()
    rz_configured = payment.is_configured()
    
    email = EmailService()
    email_configured = email.is_configured()
    
    opencage_key = os.getenv("OPENCAGE_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    status = "healthy" if db_connected else "degraded"
    
    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "connected": db_connected,
            "configured": supabase.is_configured()
        },
        "payment_gateway": {
            "configured": rz_configured
        },
        "email_service": {
            "configured": email_configured
        },
        "geocoding": {
            "configured": bool(opencage_key)
        },
        "llm_service": {
            "configured": bool(openrouter_key)
        }
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


def send_order_confirmation_background(email_service: EmailService, supabase: SupabaseService, email: str, name: str, ref_id: str, order_id: str):
    """Fires the transaction email asynchronously in the background and writes to the email logs."""
    print(f"[BackgroundTask] Sending order confirmation email for Order {ref_id} to {email}...")
    sent = email_service.send_order_confirmation(email, name, ref_id)
    supabase.log_email(order_id, "order_confirmation", email, "sent" if sent else "failed")


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
        
        # Calculate Dasha timeline for next 10 years
        now = datetime.now()
        ten_years_later = now + timedelta(days=10 * 365)
        start_t, start_d, _ = format_datetime_for_vedastro(now.isoformat(), tz)
        end_t, end_d, _ = format_datetime_for_vedastro(ten_years_later.isoformat(), tz)
        
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
            import re
            current_year = now.year
            for major_name, major_val in dasa_timeline_raw.items():
                sub_dasas = major_val.get("SubDasas") or {}
                for sub_name, sub_val in sub_dasas.items():
                    start_readable = sub_val.get("Start", "")
                    end_readable = sub_val.get("End", "")
                    
                    # Extract year
                    match = re.search(r'\b(19|20)\d{2}\b', start_readable)
                    dasha_year = int(match.group(0)) if match else 0
                    
                    if dasha_year >= current_year:
                        start_date = start_readable[6:16] if len(start_readable) >= 16 else start_readable
                        end_date = end_readable[6:16] if len(end_readable) >= 16 else end_readable
                        dasha_timeline.append([
                            f"{major_name} - {sub_name}",
                            f"{start_date} - {end_date}",
                            "Favorable window for emotional breakthroughs and setting roots."
                        ])
                        if len(dasha_timeline) >= 3:
                            break
                if len(dasha_timeline) >= 3:
                    break
            
            # Fallback if filtering left empty
            if not dasha_timeline:
                dasha_timeline.append([dasa_now.split("-")[0], f"{dob} to Future", "Major cycle guiding long term spiritual growth."])
        
        # Formatting variables
        lagna_tags_str = lagna_tags if lagna_tags else "expressive, initiating"
        moon_nakshatra = next((d.get("PlanetConstellation", "Chitta") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Chitta")
        moon_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Libra") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Libra")
        sun_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Leo") for entry in d1_data for p, d in entry.items() if p == "Sun"), "Leo")
        rudraksha_remedy = get_rudraksha_remedy(gender, moon_sign, sun_sign)
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
        
        # Concurrent LLM calls with 200 ms pacing
        async def fetch_page(page, prompt):
            min_w, max_w = PAGE_WORD_LIMITS.get(page, (80, 120))
            raw_text = await asyncio.to_thread(
                router.generate_with_retry,
                provider=provider,
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                user_prompt=prompt,
                min_words=min_w,
                max_words=max_w,
                model=model
            )
            return page, raw_text
 
        tasks = []
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
                remedies_data=remedies_data_str, dasa_info_for_ascendant=dasa_info_str,
                rudraksha_remedy=rudraksha_remedy
            )
            
            user_prompt = USER_PROMPT_TEMPLATE.format(
                page_number=page, page_instruction=instruction,
                name=name, gender=gender,
                birth_details=f"{dob} at {tob} in {place}"
            )
            
            task = asyncio.create_task(fetch_page(page, user_prompt))
            tasks.append(task)
            
            if idx < len(pages_to_generate) - 1:
                await asyncio.sleep(0.2)
                
        results = await asyncio.gather(*tasks)
        for page, text in results:
            sections_text[page] = text
            
        # Parse Rudraksha dynamic name and link
        rud_parts = rudraksha_remedy.split(" - ")
        rud_name = rud_parts[0].strip().replace("mukhi", "Mukhi")
        rud_url = rud_parts[1].strip() if len(rud_parts) > 1 else ""

        # Overwrite/assemble Page 24 Remedies content with 4 structured sections
        astrology_remedies_para = sections_text.get(24, "").strip()
        # Clean any bullet marks or raw URLs in case LLM generated them
        astrology_remedies_para = "\n".join([line for line in astrology_remedies_para.split("\n") if "astrosavvysingh" not in line])
        for marker in ["*", "-", "1.", "2.", "3.", "•"]:
            astrology_remedies_para = astrology_remedies_para.replace(marker, "")
        astrology_remedies_para = astrology_remedies_para.strip()

        # Truncate astrology remedies text to maximum ~35 words (~2-3 lines of text)
        words = astrology_remedies_para.split()
        if len(words) > 35:
            astrology_remedies_para = " ".join(words[:35]) + "..."

        # Section 1: Personalised spiritual remedies
        header1 = "§Your personalised spiritual remedies"
        para1 = f"❤ {astrology_remedies_para} For a more detailed analysis, click here to get a live consultation."

        # Section 2: Love energy bracelet
        header2 = "§Your personalised love energy bracelet"
        para2 = f"❤ To align the Venusian flow of love and soften emotional boundaries, we highly recommend wearing the sacred Divy Love Bracelet."

        # Section 3: Energised rudraksh
        header3 = "§Your personalised energised rudraksh"
        para3 = f"❤ Highly recommend you wearing the authentic {rud_name} energised and charged for you by our expert astrologer through sacred rituals."

        # Section 4: Gemstone + consultation (merged)
        header4 = "§Gem stone recommendations"
        para4 = "Your personalised Love energy stone to boost your love life, heal heartbreaks and bring to you, your desired partner. For personalised compatibility analysis and gem stone recommendations, book your one on one premium personalised consultation with our expert today."

        # Combine into 4 sections
        remedies_block = f"{header1}\n{para1}\n\n{header2}\n{para2}\n\n{header3}\n{para3}\n\n{header4}\n{para4}"
        sections_text[24] = remedies_block
            
        # PDF compilation via PDFService
        # Redirect output writes to '/tmp' on read-only environments like Vercel
        if os.getenv("VERCEL") or os.environ.get("AMAZON_AWS_LAMBDA_STAGE") or not os.access(".", os.W_OK):
            output_dir = "/tmp/output"
        else:
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
            rudraksha_name=rud_name,
            rudraksha_url=rud_url,
        )
        
        # Validate PDF structure and pages before uploading
        validate_pdf(pdf_path)
        
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
    """Search locations using OpenCage API directly for sub-second autocomplete latency, with caching."""
    if not q or not q.strip():
        return {"results": []}
        
    query_key = q.strip().lower()
    if len(query_key) < 2:
        return {"results": []}
        
    # 1. Check in-memory cache
    if query_key in geocode_mem_cache:
        return {"results": geocode_mem_cache[query_key]}
        
    # 2. Check file cache
    cached_data = geocode_file_cache.get(query_key)
    if cached_data is not None:
        geocode_mem_cache[query_key] = cached_data
        return {"results": cached_data}
        
    # 3. Query OpenCage API using pre-initialized client
    try:
        results = geocoder_client.geocode(q, no_annotations=0, limit=5)
        if not results:
            return {"results": []}
            
        formatted_results = []
        for r in results:
            geometry = r.get("geometry", {})
            annotations = r.get("annotations", {})
            timezone_info = annotations.get("timezone", {})
            
            formatted_results.append({
                "formatted": r.get("formatted"),
                "latitude": geometry.get("lat"),
                "longitude": geometry.get("lng"),
                "timezone": timezone_info.get("name") or "Asia/Kolkata",
                "raw": r
            })
            
        # Store in caches
        geocode_file_cache.set(query_key, formatted_results)
        geocode_mem_cache[query_key] = formatted_results
        
        return {"results": formatted_results}
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
async def api_create_order(payload: Dict[str, Any]):
    """Register customer, record order in Supabase, and spawn Razorpay Order ID, or authenticate admin."""
    supabase = SupabaseService()
    payment_service = PaymentService()
    
    # 1. Admin login interceptor (for backward compatibility with admin_login.html)
    if payload.get("auth_admin"):
        email = payload.get("email", "")
        password = payload.get("password", "")
        try:
            session = supabase.sign_in_with_password(email, password)
            if not session:
                raise HTTPException(status_code=401, detail="Invalid admin credentials.")
            return session
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))
        
    try:
        req = CreateOrderRequest(**payload)
        # 2. Customer signup / resolve
        customer_id = supabase.get_or_create_customer(req.name, req.email, req.mobile)
        
        # 3. Append gender to geocoded metadata
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
        
        order_details = supabase.get_order_by_id(order_id)
        ref_id = order_details.get("reference_id") if order_details else "AS-1234"
        
        # 4. Generate Razorpay Order
        rz_order = payment_service.create_razorpay_order(499.00, order_id)
        supabase.create_payment(order_id, rz_order["id"], 499.00)
        
        return {
            "order_id": order_id,
            "reference_id": ref_id,
            "razorpay_order_id": rz_order["id"],
            "amount": rz_order["amount"],
            "currency": "INR",
            "razorpay_key_id": os.getenv("RAZORPAY_KEY_ID", "")
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
        # 2. Confirm Payment details & capture atomically
        was_pending = supabase.confirm_order_payment_atomic(req.order_id)
        if was_pending:
            try:
                supabase.confirm_payment(req.razorpay_order_id, req.razorpay_payment_id, req.model_dump())
            except Exception as pe:
                print(f"[VerifyPayment Error] Failed to save payments log (likely unique constraint): {pe}")
            
            # Calculate and set scheduled delivery time
            scheduled_at = calculate_delivery_time_ist(datetime.now(timezone.utc))
            supabase.set_scheduled_delivery(req.order_id, scheduled_at)

            order = supabase.get_order_by_id(req.order_id)
            if not order:
                print(f"[VerifyPayment] Order {req.order_id} not found in database. Using mock fallback details.")
                cust = {
                    "full_name": "Valued Customer",
                    "email": "customer@example.com"
                }
                ref_id = "AS-1234"
            else:
                cust = order.get("customers") or {}
                ref_id = order.get("reference_id") or req.order_id[-8:]
            
            # 3. Fire immediate 24-36 hour confirmation email in background
            background_tasks.add_task(
                send_order_confirmation_background,
                email_service, supabase, cust["email"], cust["full_name"], ref_id, req.order_id
            )
            
            # 4. Spawn background async report generation task
            background_tasks.add_task(
                generate_report_background_task,
                order_id=req.order_id,
                provider="openrouter",
                model=None
            )
            return {"status": "success", "detail": "Payment captured and order generation started."}
        else:
            print(f"[VerifyPayment] Order {req.order_id} was already confirmed paid. Skipping duplicate actions.")
            return {"status": "success", "detail": "Payment already processed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/payments/webhook")
async def api_payments_webhook(request: Request, background_tasks: BackgroundTasks):
    """Secure webhook endpoint listening to order.paid or payment.captured events from Razorpay."""
    # Read raw body bytes
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    
    # Get signature header
    signature = request.headers.get("X-Razorpay-Signature", "")
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
    
    if not secret:
        print("[Webhook] RAZORPAY_WEBHOOK_SECRET not set in environment.")
        raise HTTPException(status_code=400, detail="Webhook secret not configured.")
        
    payment_service = PaymentService()
    verified = payment_service.verify_webhook_signature(body_str, signature, secret)
    if not verified:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")
        
    # Process event payload
    try:
        payload = json.loads(body_str)
        event = payload.get("event")
        
        # We process order.paid (Razorpay order completed and paid)
        if event == "order.paid":
            entity = payload.get("payload", {}).get("order", {}).get("entity", {})
            rz_order_id = entity.get("id")
            
            # Fetch order from Supabase by rz_order_id
            supabase = SupabaseService()
            order = supabase.get_order_by_rz_id(rz_order_id)
            if order:
                order_id = order["id"]
                # Only execute if the order has not been fulfilled already
                if order["order_status"] not in ["paid", "processing", "completed", "delivered"]:
                    print(f"[Webhook] Fulfilling order {order_id} via webhook...")
                    
                    # 1. Update status atomically
                    was_pending = supabase.confirm_order_payment_atomic(order_id)
                    if was_pending:
                        # Get payment details from payments array inside payload if available
                        payments_list = payload.get("payload", {}).get("payments", [])
                        rz_payment_id = f"webhook_{rz_order_id[-8:]}"
                        if payments_list:
                            rz_payment_id = payments_list[0].get("entity", {}).get("id", f"webhook_{rz_order_id[-8:]}")
                        
                        try:
                            supabase.confirm_payment(rz_order_id, rz_payment_id, payload)
                        except Exception as pe:
                            print(f"[Webhook Error] Failed to save payments log (likely unique constraint): {pe}")
                        
                        # Calculate and set scheduled delivery time
                        scheduled_at = calculate_delivery_time_ist(datetime.now(timezone.utc))
                        supabase.set_scheduled_delivery(order_id, scheduled_at)

                        # 2. Fire immediate 24-36 hour confirmation email in background
                        email_service = EmailService()
                        cust = order.get("customers") or {}
                        ref_id = order.get("reference_id") or order_id[-8:]
                        background_tasks.add_task(
                            send_order_confirmation_background,
                            email_service, supabase, cust["email"], cust["full_name"], ref_id, order_id
                        )
                        
                        # 3. Spawn background async report generation task
                        background_tasks.add_task(
                            generate_report_background_task,
                            order_id=order_id,
                            provider="openrouter",
                            model=None
                        )
                    else:
                        print(f"[Webhook] Order {order_id} was already confirmed paid. Skipping duplicate actions.")
        return {"status": "accepted"}
    except Exception as e:
        print(f"[Webhook Error] {e}")
        return {"status": "error", "detail": str(e)}

def get_admin_role(user: Dict[str, Any]) -> str:
    """Helper to extract admin user role: 'admin' or 'support'."""
    email = user.get("email", "").lower()
    metadata = user.get("user_metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}
    
    role = metadata.get("role") or user.get("role") or ""
    if role == "support" or "support" in email:
        return "support"
    return "admin"


@app.get("/api/admin/orders")
async def api_admin_orders(status: Optional[str] = None, search: Optional[str] = None, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    role = get_admin_role(user)
    
    supabase = SupabaseService()
    orders = supabase.get_orders(status, search)
    
    # Secure role-based filtering: Customer Support gets a clean truncated view
    if role == "support":
        truncated_orders = []
        for o in orders:
            cust = o.get("customers") or {}
            truncated_orders.append({
                "id": o.get("id"),
                "order_status": o.get("order_status"),
                "report_status": o.get("report_status"),
                "created_at": o.get("created_at"),
                "customers": {
                    "full_name": cust.get("full_name"),
                    "email": cust.get("email"),
                    "mobile": cust.get("mobile")
                }
            })
        return {"orders": truncated_orders, "role": role}
        
    return {"orders": orders, "role": role}


@app.get("/api/admin/orders/{order_id}")
async def api_admin_order_detail(order_id: str, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    role = get_admin_role(user)
    
    supabase = SupabaseService()
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # Secure detail truncation for Customer Support
    if role == "support":
        cust = order.get("customers") or {}
        truncated_order = {
            "id": order.get("id"),
            "reference_id": order.get("reference_id"),
            "order_status": order.get("order_status"),
            "report_status": order.get("report_status"),
            "created_at": order.get("created_at"),
            "customers": {
                "full_name": cust.get("full_name"),
                "email": cust.get("email"),
                "mobile": cust.get("mobile")
            },
            "payments": order.get("payments") or []
        }
        return {"order": truncated_order, "email_logs": [], "role": role}
        
    logs = supabase.get_email_logs(order_id)
    return {"order": order, "email_logs": logs, "role": role}


class UpdateNotesRequest(BaseModel):
    notes: str

@app.post("/api/admin/orders/{order_id}/notes")
async def api_admin_update_notes(order_id: str, req: UpdateNotesRequest, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    if get_admin_role(user) == "support":
        raise HTTPException(status_code=403, detail="Forbidden: Customer Support role cannot perform write actions.")
        
    supabase = SupabaseService()
    success = supabase.save_admin_notes(order_id, req.notes)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save admin notes")
    return {"status": "success"}


class UpdateStatusRequest(BaseModel):
    status: str

@app.post("/api/admin/orders/{order_id}/status")
async def api_admin_update_status(order_id: str, req: UpdateStatusRequest, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    if get_admin_role(user) == "support":
        raise HTTPException(status_code=403, detail="Forbidden: Customer Support role cannot perform write actions.")
        
    supabase = SupabaseService()
    success = supabase.update_order_status(order_id, req.status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update order status")
    return {"status": "success"}


@app.post("/api/admin/orders/{order_id}/generate")
async def api_admin_trigger_generate(order_id: str, background_tasks: BackgroundTasks, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    if get_admin_role(user) == "support":
        raise HTTPException(status_code=403, detail="Forbidden: Customer Support role cannot perform write actions.")
        
    supabase = SupabaseService()
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    background_tasks.add_task(
        generate_report_background_task,
        order_id=order_id,
        provider="openrouter",
        model=None
    )
    return {"status": "success", "detail": "Async report generation re-triggered."}


class ManualUploadRequest(BaseModel):
    report_url: str

@app.post("/api/admin/orders/{order_id}/upload")
async def api_admin_manual_upload(order_id: str, req: ManualUploadRequest, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    if get_admin_role(user) == "support":
        raise HTTPException(status_code=403, detail="Forbidden: Customer Support role cannot perform write actions.")
        
    supabase = SupabaseService()
    success = supabase.update_order_report(order_id, req.report_url)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to upload manual report url")
    return {"status": "success"}


@app.post("/api/admin/orders/{order_id}/resend-confirmation")
async def api_admin_resend_confirmation(order_id: str, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    if get_admin_role(user) == "support":
        raise HTTPException(status_code=403, detail="Forbidden: Customer Support role cannot perform write actions.")
        
    supabase = SupabaseService()
    email_service = EmailService()
    
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    cust = order.get("customers") or {}
    ref_id = order.get("reference_id") or order_id[-8:]
    sent = email_service.send_order_confirmation(cust["email"], cust["full_name"], ref_id)
    supabase.log_email(order_id, "order_confirmation", cust["email"], "sent" if sent else "failed")
    
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to resend confirmation email")
    return {"status": "success"}


@app.post("/api/admin/orders/{order_id}/send-report")
async def api_admin_send_report(order_id: str, admin: Any = Header(None)):
    user = await get_current_admin(admin)
    if get_admin_role(user) == "support":
        raise HTTPException(status_code=403, detail="Forbidden: Customer Support role cannot perform write actions.")
        
    supabase = SupabaseService()
    email_service = EmailService()
    
    order = supabase.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    if not order.get("report_url"):
        raise HTTPException(status_code=400, detail="Report has not been generated yet.")
        
    cust = order.get("customers") or {}
    ref_id = order.get("reference_id") or order_id[-8:]
    filename = f"Love_Report_{ref_id}.pdf"
    
    # Retrieve PDF bytes from local disk or Supabase URL to attach to email
    pdf_bytes = None
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", f"Love_Report_{order_id}.pdf"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", f"Love_Report_{ref_id}.pdf")
    ]
    for p in possible_paths:
        if os.path.exists(p):
            try:
                with open(p, "rb") as f:
                    pdf_bytes = f.read()
                break
            except Exception:
                pass
                
    if not pdf_bytes and order.get("report_url"):
        try:
            res = requests.get(order["report_url"], timeout=15)
            if res.status_code == 200:
                pdf_bytes = res.content
        except Exception as e:
            print(f"[SendReport] Failed to fetch PDF bytes from URL: {e}")

    sent = email_service.send_report_delivered(cust["email"], cust["full_name"], ref_id, order["report_url"], pdf_bytes=pdf_bytes, pdf_filename=filename)
    supabase.log_email(order_id, "report_delivered", cust["email"], "sent" if sent else "failed")
    
    if sent:
        supabase.update_order_status(order_id, "delivered")
        return {"status": "success"}
    else:
        raise HTTPException(status_code=500, detail="Email delivery failed")


# --- Admin User Management Endpoints ---

class AdminSignupRequest(BaseModel):
    full_name: str
    email: str
    password: str

@app.post("/api/admin/signup")
async def api_admin_signup(req: AdminSignupRequest):
    """Sign up a new admin user as pending support."""
    supabase = SupabaseService()
    success = supabase.sign_up_admin(req.email, req.password, req.full_name)
    if not success:
        raise HTTPException(status_code=400, detail="Registration failed. Email may already be registered.")
    return {"status": "success", "detail": "User registered successfully, pending approval."}


@app.get("/api/admin/users")
async def api_admin_list_users(admin: Any = Header(None)):
    """List all admin users (Admin role only)."""
    user = await get_current_admin(admin)
    if get_admin_role(user) != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Full Admin privileges required.")
        
    supabase = SupabaseService()
    users = supabase.list_admin_users()
    return {"users": users}


class ApproveUserRequest(BaseModel):
    status: str  # approved or rejected

@app.post("/api/admin/users/{email}/approve")
async def api_admin_approve_user(email: str, req: ApproveUserRequest, admin: Any = Header(None)):
    """Approve or reject a pending admin user (Admin role only)."""
    user = await get_current_admin(admin)
    if get_admin_role(user) != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Full Admin privileges required.")
        
    if req.status not in ["approved", "rejected", "pending"]:
        raise HTTPException(status_code=400, detail="Invalid status value.")
        
    supabase = SupabaseService()
    success = supabase.update_admin_user_status(email, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "success", "detail": f"User status updated to {req.status}."}


class UpdateUserRoleRequest(BaseModel):
    role: str  # admin or support

@app.post("/api/admin/users/{email}/role")
async def api_admin_update_user_role(email: str, req: UpdateUserRoleRequest, admin: Any = Header(None)):
    """Change an admin user's role (Admin role only)."""
    user = await get_current_admin(admin)
    if get_admin_role(user) != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Full Admin privileges required.")
        
    if req.role not in ["admin", "support"]:
        raise HTTPException(status_code=400, detail="Invalid role value.")
        
    supabase = SupabaseService()
    success = supabase.update_admin_user_role(email, req.role)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "success", "detail": f"User role updated to {req.role}."}


@app.delete("/api/admin/users/{email}")
async def api_admin_delete_user(email: str, admin: Any = Header(None)):
    """Delete an admin user (Admin role only)."""
    user = await get_current_admin(admin)
    if get_admin_role(user) != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Full Admin privileges required.")
        
    supabase = SupabaseService()
    success = supabase.delete_admin_user(email)
    if not success:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"status": "success", "detail": "User deleted successfully."}


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
        ten_years_later = now + timedelta(days=10 * 365)
        start_t, start_d, _ = format_datetime_for_vedastro(now.isoformat(), tz)
        end_t, end_d, _ = format_datetime_for_vedastro(ten_years_later.isoformat(), tz)
        
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
            import re
            current_year = now.year
            for major_name, major_val in dasa_timeline_raw.items():
                sub_dasas = major_val.get("SubDasas") or {}
                for sub_name, sub_val in sub_dasas.items():
                    start_readable = sub_val.get("Start", "")
                    end_readable = sub_val.get("End", "")
                    
                    # Extract year
                    match = re.search(r'\b(19|20)\d{2}\b', start_readable)
                    dasha_year = int(match.group(0)) if match else 0
                    
                    if dasha_year >= current_year:
                        start_date = start_readable[6:16] if len(start_readable) >= 16 else start_readable
                        end_date = end_readable[6:16] if len(end_readable) >= 16 else end_readable
                        dasha_timeline.append([
                            f"{major_name} - {sub_name}",
                            f"{start_date} - {end_date}",
                            "Favorable window for emotional breakthroughs and setting roots."
                        ])
                        if len(dasha_timeline) >= 3:
                            break
                if len(dasha_timeline) >= 3:
                    break
            
            # Fallback if filtering left empty
            if not dasha_timeline:
                dasha_timeline.append([dasa_now.split("-")[0], f"{req.dob} to Future", "Major cycle guiding long term spiritual growth."])
                
        lagna_tags_str = lagna_tags if lagna_tags else "expressive, initiating"
        moon_nakshatra = next((d.get("PlanetConstellation", "Chitta") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Chitta")
        moon_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Libra") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Libra")
        sun_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Leo") for entry in d1_data for p, d in entry.items() if p == "Sun"), "Leo")
        rudraksha_remedy = get_rudraksha_remedy(req.gender, moon_sign, sun_sign)
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
        
        # Concurrent LLM calls with 200 ms pacing
        async def fetch_page(page, prompt):
            min_w, max_w = PAGE_WORD_LIMITS.get(page, (80, 120))
            raw_text = await asyncio.to_thread(
                router.generate_with_retry,
                provider=req.provider,
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                user_prompt=prompt,
                min_words=min_w,
                max_words=max_w,
                model=req.model
            )
            return page, raw_text

        tasks = []
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
                remedies_data=remedies_data_str, dasa_info_for_ascendant=dasa_info_str,
                rudraksha_remedy=rudraksha_remedy
            )
            
            user_prompt = USER_PROMPT_TEMPLATE.format(
                page_number=page, page_instruction=instruction,
                name=req.name, gender=req.gender,
                birth_details=f"{req.dob} at {req.tob} in {req.place}"
            )
            
            task = asyncio.create_task(fetch_page(page, user_prompt))
            tasks.append(task)
            
            if idx < len(pages_to_generate) - 1:
                await asyncio.sleep(0.2)
                
        results = await asyncio.gather(*tasks)
        for page, text in results:
            sections_text[page] = text
            
        # Parse Rudraksha dynamic name and link
        rud_parts = rudraksha_remedy.split(" - ")
        rud_name = rud_parts[0].strip().replace("mukhi", "Mukhi")
        rud_url = rud_parts[1].strip() if len(rud_parts) > 1 else ""

        # Overwrite/assemble Page 24 Remedies content with 4 structured sections
        astrology_remedies_para = sections_text.get(24, "").strip()
        astrology_remedies_para = "\n".join([line for line in astrology_remedies_para.split("\n") if "astrosavvysingh" not in line])
        for marker in ["*", "-", "1.", "2.", "3.", "•"]:
            astrology_remedies_para = astrology_remedies_para.replace(marker, "")
        astrology_remedies_para = astrology_remedies_para.strip()

        words = astrology_remedies_para.split()
        if len(words) > 35:
            astrology_remedies_para = " ".join(words[:35]) + "..."

        header1 = "§Your personalised spiritual remedies"
        para1 = f"❤ {astrology_remedies_para} For a more detailed analysis, click here to get a live consultation."

        header2 = "§Your personalised love energy bracelet"
        para2 = f"❤ To align the Venusian flow of love and soften emotional boundaries, we highly recommend wearing the sacred Divy Love Bracelet."

        header3 = "§Your personalised energised rudraksh"
        para3 = f"❤ Highly recommend you wearing the authentic {rud_name} energised and charged for you by our expert astrologer through sacred rituals."

        header4 = "§Gem stone recommendations"
        para4 = "Your personalised Love energy stone to boost your love life, heal heartbreaks and bring to you, your desired partner. For personalised compatibility analysis and gem stone recommendations, book your one on one premium personalised consultation with our expert today."

        remedies_block = f"{header1}\n{para1}\n\n{header2}\n{para2}\n\n{header3}\n{para3}\n\n{header4}\n{para4}"
        sections_text[24] = remedies_block
            
        # Redirect output writes to '/tmp' on read-only environments like Vercel
        if os.getenv("VERCEL") or os.environ.get("AMAZON_AWS_LAMBDA_STAGE") or not os.access(".", os.W_OK):
            output_dir = "/tmp/output"
        else:
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
            rudraksha_name=rud_name,
            rudraksha_url=rud_url,
        )
        
        # Validate PDF structure and pages before returning
        validate_pdf(pdf_path)
        
        return FileResponse(pdf_path, media_type="application/pdf", filename=f"{req.name.lower()}_individual_love_report.pdf")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


async def run_scheduled_delivery_logic():
    """Queries, auto-delivers, and transitions processing orders that are past their scheduled IST delivery time."""
    supabase = SupabaseService()
    if not supabase.is_configured():
        return
        
    email_service = EmailService()
    now_utc = datetime.now(timezone.utc)
    
    try:
        # Fetch processing orders
        res = supabase.client.table("orders").select("*, customers(*)").eq("order_status", "processing").execute()
        orders = res.data or []
        
        for o in orders:
            report_url = o.get("report_url")
            scheduled_str = o.get("scheduled_delivery_at")
            
            if not report_url or not scheduled_str:
                continue
                
            try:
                # Parse ISO string
                scheduled_at = datetime.fromisoformat(scheduled_str.replace("Z", "+00:00"))
            except Exception:
                continue
                
            if scheduled_at <= now_utc:
                cust = o.get("customers") or {}
                ref_id = o.get("reference_id") or o["id"][-8:]
                email = cust.get("email")
                name = cust.get("full_name", "Customer")
                
                if email:
                    print(f"[CronWorker] Auto-delivering report for Order {o['id']} scheduled for {scheduled_str}")
                    sent = email_service.send_report_delivered(email, name, ref_id, report_url)
                    supabase.log_email(o["id"], "report_delivered", email, "sent" if sent else "failed")
                    if sent:
                        supabase.update_order_status(o["id"], "delivered")
    except Exception as e:
        print(f"[CronWorker] Error checking/delivering scheduled reports: {e}")


@app.get("/api/cron/send-reports")
async def api_cron_send_reports():
    """Cron endpoint triggered by external schedulers (e.g. Vercel Cron Jobs) to process report deliveries."""
    await run_scheduled_delivery_logic()
    return {"status": "success", "detail": "Scheduled report delivery worker executed."}


async def local_scheduled_worker_loop():
    """Local worker loop that periodically checks database for due reports."""
    print("[LocalWorker] Background scheduler started.")
    while True:
        try:
            await run_scheduled_delivery_logic()
        except Exception as e:
            print(f"[LocalWorker] Error in local worker: {e}")
        await asyncio.sleep(60) # check every minute


@app.on_event("startup")
async def startup_event():
    # Only start local thread if we are not running under a serverless environment
    if not os.getenv("VERCEL") and not os.environ.get("AMAZON_AWS_LAMBDA_STAGE"):
        asyncio.create_task(local_scheduled_worker_loop())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
