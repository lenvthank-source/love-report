-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Customers Table
CREATE TABLE IF NOT EXISTS public.customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    mobile TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_customers_email ON public.customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_mobile ON public.customers(mobile);

-- 2. Orders Table
CREATE TABLE IF NOT EXISTS public.orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reference_id TEXT UNIQUE,
    customer_id UUID REFERENCES public.customers(id) ON DELETE CASCADE,
    dob DATE NOT NULL,
    tob TIME NOT NULL,
    place TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    timezone TEXT NOT NULL,
    geocoded_place JSONB NOT NULL,
    order_status TEXT NOT NULL DEFAULT 'pending', -- pending, paid, processing, completed, failed, cancelled, refunded
    report_status TEXT NOT NULL DEFAULT 'not_started', -- not_started, generating, completed, failed
    report_url TEXT,
    notes TEXT,
    scheduled_delivery_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_status ON public.orders(order_status);
CREATE INDEX IF NOT EXISTS idx_orders_created ON public.orders(created_at DESC);

-- 3. Payments Table
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES public.orders(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL DEFAULT 999.00,
    razorpay_order_id TEXT NOT NULL UNIQUE,
    razorpay_payment_id TEXT UNIQUE,
    payment_status TEXT NOT NULL DEFAULT 'created', -- created, authorized, captured, failed, refunded
    paid_at TIMESTAMPTZ,
    raw_response JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_payments_razorpay_order ON public.payments(razorpay_order_id);

-- 4. Email Logs Table
CREATE TABLE IF NOT EXISTS public.email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES public.orders(id) ON DELETE CASCADE,
    template_name TEXT NOT NULL,
    recipient_email TEXT NOT NULL,
    status TEXT NOT NULL, -- sent, failed
    error_message TEXT,
    sent_at TIMESTAMPTZ DEFAULT now()
);

-- 5. Admin Users Table
CREATE TABLE IF NOT EXISTS public.admin_users (
    email TEXT PRIMARY KEY,
    full_name TEXT,
    role TEXT NOT NULL DEFAULT 'support', -- admin, support
    status TEXT NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_admin_users_status ON public.admin_users(status);
ALTER TABLE public.admin_users DISABLE ROW LEVEL SECURITY;

-- DDL migrations for existing databases
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS reference_id TEXT UNIQUE;
ALTER TABLE public.orders ADD COLUMN IF NOT EXISTS scheduled_delivery_at TIMESTAMPTZ;

-- Timezone-aware scheduling helper function
CREATE OR REPLACE FUNCTION public.calculate_delivery_time_ist(order_time_utc TIMESTAMPTZ)
RETURNS TIMESTAMPTZ AS $$
DECLARE
    current_ist TIMESTAMP;
    remaining_delay_minutes INT := 240; -- 4 hours
    window_start TIMESTAMP;
    window_end TIMESTAMP;
    minutes_left_in_window INT;
BEGIN
    current_ist := order_time_utc AT TIME ZONE 'Asia/Kolkata';
    
    WHILE remaining_delay_minutes > 0 LOOP
        window_start := date_trunc('day', current_ist) + INTERVAL '11 hours';
        window_end := date_trunc('day', current_ist) + INTERVAL '19 hours';
        
        IF current_ist < window_start THEN
            current_ist := window_start;
        ELSIF current_ist >= window_end THEN
            current_ist := date_trunc('day', current_ist) + INTERVAL '1 day 11 hours';
        ELSE
            minutes_left_in_window := EXTRACT(EPOCH FROM (window_end - current_ist)) / 60;
            IF remaining_delay_minutes <= minutes_left_in_window THEN
                current_ist := current_ist + (remaining_delay_minutes || ' minutes')::INTERVAL;
                remaining_delay_minutes := 0;
            ELSE
                remaining_delay_minutes := remaining_delay_minutes - minutes_left_in_window;
                current_ist := date_trunc('day', current_ist) + INTERVAL '1 day 11 hours';
            END IF;
        END IF;
    END LOOP;
    
    RETURN current_ist AT TIME ZONE 'Asia/Kolkata';
END;
$$ LANGUAGE plpgsql;


