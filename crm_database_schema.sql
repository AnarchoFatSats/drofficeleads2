-- Cura Genesis CRM Database Schema
-- PostgreSQL 14+

-- Create database
-- CREATE DATABASE cura_genesis_crm;

-- ===================================================================
-- USERS & AUTHENTICATION
-- ===================================================================

-- User roles enum
CREATE TYPE user_role AS ENUM ('admin', 'agent', 'manager');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'suspended');

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role user_role NOT NULL DEFAULT 'agent',
    status user_status NOT NULL DEFAULT 'active',
    territory_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP WITH TIME ZONE
);

-- User sessions for JWT management
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- ===================================================================
-- TERRITORIES & ASSIGNMENTS
-- ===================================================================

-- Territories
CREATE TABLE territories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    states TEXT[], -- Array of state codes
    zip_codes TEXT[], -- Array of ZIP codes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===================================================================
-- ENHANCED LEADS SYSTEM (Preserving Your Scoring)
-- ===================================================================

-- Lead status enum
CREATE TYPE lead_status AS ENUM ('new', 'assigned', 'contacted', 'qualified', 'demo_scheduled', 'proposal_sent', 'negotiation', 'closed_won', 'closed_lost', 'recycled');
CREATE TYPE lead_priority AS ENUM ('A+', 'A', 'B+', 'B', 'C');
CREATE TYPE lead_source AS ENUM ('nppes_extraction', 'manual_entry', 'referral', 'marketing', 'recycled');

-- Enhanced Leads table (preserving your existing structure)
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    
    -- Original NPPES Data (Your Existing Fields)
    npi VARCHAR(20) UNIQUE,
    ein VARCHAR(20),
    practice_name VARCHAR(500),
    owner_name VARCHAR(200),
    practice_phone VARCHAR(20),
    owner_phone VARCHAR(20),
    specialties TEXT,
    category VARCHAR(100),
    providers INTEGER DEFAULT 1,
    city VARCHAR(100),
    state VARCHAR(2),
    zip_code VARCHAR(10),
    address TEXT,
    entity_type VARCHAR(50),
    is_sole_proprietor BOOLEAN,
    
    -- Your Scoring System (Preserved)
    score INTEGER NOT NULL DEFAULT 0,
    priority lead_priority NOT NULL,
    medicare_allograft_score INTEGER DEFAULT 0,
    overlooked_opportunity_score INTEGER DEFAULT 0,
    rural_verified_score INTEGER DEFAULT 0,
    scoring_breakdown JSONB, -- Store detailed scoring explanation
    
    -- CRM Enhancement Fields
    status lead_status NOT NULL DEFAULT 'new',
    source lead_source NOT NULL DEFAULT 'nppes_extraction',
    assigned_to INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE,
    territory_id INTEGER REFERENCES territories(id),
    
    -- Lead Lifecycle Management
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    first_contacted_at TIMESTAMP WITH TIME ZONE,
    last_contacted_at TIMESTAMP WITH TIME ZONE,
    qualified_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE,
    
    -- 7-Day Recycling System
    recycling_eligible_at TIMESTAMP WITH TIME ZONE,
    times_recycled INTEGER DEFAULT 0,
    previous_agents INTEGER[], -- Track who has worked this lead
    
    -- Business Intelligence
    estimated_deal_value DECIMAL(10,2),
    probability INTEGER CHECK (probability >= 0 AND probability <= 100),
    expected_close_date DATE,
    
    -- Tracking
    view_count INTEGER DEFAULT 0,
    contact_attempts INTEGER DEFAULT 0,
    
    -- Search & Performance
    search_vector tsvector
);

-- ===================================================================
-- ACTIVITIES & INTERACTIONS
-- ===================================================================

CREATE TYPE activity_type AS ENUM ('call', 'email', 'meeting', 'note', 'task', 'demo', 'proposal', 'follow_up');
CREATE TYPE activity_outcome AS ENUM ('connected', 'voicemail', 'no_answer', 'busy', 'scheduled', 'completed', 'cancelled');

-- Activities tracking
CREATE TABLE activities (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    type activity_type NOT NULL,
    outcome activity_outcome,
    
    -- Activity Details
    subject VARCHAR(200),
    description TEXT,
    notes TEXT,
    
    -- Timing
    scheduled_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    
    -- Email specific
    email_opened BOOLEAN DEFAULT false,
    email_clicked BOOLEAN DEFAULT false,
    
    -- Call specific
    call_recording_url VARCHAR(500),
    
    -- Meeting specific
    meeting_url VARCHAR(500),
    attendees JSONB,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===================================================================
-- TASKS & FOLLOW-UPS
-- ===================================================================

CREATE TYPE task_status AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'overdue');
CREATE TYPE task_priority AS ENUM ('low', 'medium', 'high', 'urgent');

-- Tasks table
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    assigned_to INTEGER REFERENCES users(id),
    created_by INTEGER REFERENCES users(id),
    
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status task_status NOT NULL DEFAULT 'pending',
    priority task_priority NOT NULL DEFAULT 'medium',
    
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Auto-generated tasks (like recycling reminders)
    is_automated BOOLEAN DEFAULT false,
    automation_rule VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===================================================================
-- GAMIFICATION SYSTEM
-- ===================================================================

-- Points tracking
CREATE TABLE user_points (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    lead_id INTEGER REFERENCES leads(id),
    activity_id INTEGER REFERENCES activities(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Badges/Achievements
CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    points_required INTEGER,
    conditions JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User badge achievements
CREATE TABLE user_badges (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    badge_id INTEGER REFERENCES badges(id),
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    lead_id INTEGER REFERENCES leads(id)
);

-- Leaderboards (aggregated daily)
CREATE TABLE leaderboard_entries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_points INTEGER DEFAULT 0,
    calls_made INTEGER DEFAULT 0,
    emails_sent INTEGER DEFAULT 0,
    meetings_scheduled INTEGER DEFAULT 0,
    leads_qualified INTEGER DEFAULT 0,
    deals_closed INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- ===================================================================
-- REAL-TIME NOTIFICATIONS
-- ===================================================================

CREATE TYPE notification_type AS ENUM ('new_lead', 'lead_assigned', 'task_due', 'lead_recycled', 'achievement', 'system');
CREATE TYPE notification_status AS ENUM ('unread', 'read', 'dismissed');

-- Notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type notification_type NOT NULL,
    status notification_status NOT NULL DEFAULT 'unread',
    
    title VARCHAR(200) NOT NULL,
    message TEXT,
    action_url VARCHAR(500),
    
    lead_id INTEGER REFERENCES leads(id),
    activity_id INTEGER REFERENCES activities(id),
    task_id INTEGER REFERENCES tasks(id),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    read_at TIMESTAMP WITH TIME ZONE
);

-- ===================================================================
-- LEAD RECYCLING AUTOMATION
-- ===================================================================

-- Lead assignment history
CREATE TABLE lead_assignments (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    unassigned_at TIMESTAMP WITH TIME ZONE,
    reason VARCHAR(100), -- 'recycled', 'manual_reassign', 'territory_change'
    notes TEXT
);

-- Recycling rules configuration
CREATE TABLE recycling_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    priority_levels lead_priority[],
    days_without_contact INTEGER DEFAULT 7,
    min_contact_attempts INTEGER DEFAULT 3,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===================================================================
-- ANALYTICS & REPORTING
-- ===================================================================

-- Lead scoring history (track changes over time)
CREATE TABLE lead_scoring_history (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    priority lead_priority NOT NULL,
    scoring_algorithm VARCHAR(50),
    changes JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance metrics (aggregated)
CREATE TABLE performance_metrics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    leads_assigned INTEGER DEFAULT 0,
    leads_contacted INTEGER DEFAULT 0,
    leads_qualified INTEGER DEFAULT 0,
    demos_scheduled INTEGER DEFAULT 0,
    proposals_sent INTEGER DEFAULT 0,
    deals_closed INTEGER DEFAULT 0,
    revenue_generated DECIMAL(10,2) DEFAULT 0,
    avg_response_time_hours DECIMAL(5,2),
    conversion_rate DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, date)
);

-- ===================================================================
-- SYSTEM CONFIGURATION
-- ===================================================================

-- System settings
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===================================================================
-- INDEXES FOR PERFORMANCE
-- ===================================================================

-- Users indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_territory ON users(territory_id);

-- Leads indexes
CREATE INDEX idx_leads_npi ON leads(npi);
CREATE INDEX idx_leads_assigned_to ON leads(assigned_to);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_priority ON leads(priority);
CREATE INDEX idx_leads_territory ON leads(territory_id);
CREATE INDEX idx_leads_created_at ON leads(created_at);
CREATE INDEX idx_leads_recycling_eligible ON leads(recycling_eligible_at) WHERE recycling_eligible_at IS NOT NULL;
CREATE INDEX idx_leads_search ON leads USING GIN(search_vector);

-- Activities indexes
CREATE INDEX idx_activities_lead_id ON activities(lead_id);
CREATE INDEX idx_activities_user_id ON activities(user_id);
CREATE INDEX idx_activities_type ON activities(type);
CREATE INDEX idx_activities_scheduled_at ON activities(scheduled_at);

-- Tasks indexes
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_lead_id ON tasks(lead_id);

-- Gamification indexes
CREATE INDEX idx_user_points_user_id ON user_points(user_id);
CREATE INDEX idx_user_badges_user_id ON user_badges(user_id);
CREATE INDEX idx_leaderboard_date ON leaderboard_entries(date);

-- Notifications indexes
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- ===================================================================
-- FUNCTIONS & TRIGGERS
-- ===================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply timestamp triggers
CREATE TRIGGER update_users_timestamp BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_leads_timestamp BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_activities_timestamp BEFORE UPDATE ON activities FOR EACH ROW EXECUTE FUNCTION update_timestamp();
CREATE TRIGGER update_tasks_timestamp BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- Lead recycling trigger function
CREATE OR REPLACE FUNCTION check_lead_recycling()
RETURNS TRIGGER AS $$
BEGIN
    -- Set recycling eligible date when lead is assigned
    IF NEW.assigned_to IS NOT NULL AND OLD.assigned_to IS NULL THEN
        NEW.recycling_eligible_at = NOW() + INTERVAL '7 days';
    END IF;
    
    -- Clear recycling date when lead progresses or closes
    IF NEW.status IN ('qualified', 'demo_scheduled', 'proposal_sent', 'negotiation', 'closed_won', 'closed_lost') THEN
        NEW.recycling_eligible_at = NULL;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER lead_recycling_trigger BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION check_lead_recycling();

-- Search vector update function
CREATE OR REPLACE FUNCTION update_lead_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = to_tsvector('english', 
        COALESCE(NEW.practice_name, '') || ' ' ||
        COALESCE(NEW.owner_name, '') || ' ' ||
        COALESCE(NEW.specialties, '') || ' ' ||
        COALESCE(NEW.city, '') || ' ' ||
        COALESCE(NEW.state, '') || ' ' ||
        COALESCE(NEW.zip_code, '')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_lead_search_trigger BEFORE INSERT OR UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION update_lead_search_vector();

-- ===================================================================
-- INITIAL DATA
-- ===================================================================

-- Default territories
INSERT INTO territories (name, description, states) VALUES
('Northeast', 'Northeast region', ARRAY['ME', 'NH', 'VT', 'MA', 'RI', 'CT', 'NY', 'NJ', 'PA']),
('Southeast', 'Southeast region', ARRAY['DE', 'MD', 'VA', 'WV', 'KY', 'TN', 'NC', 'SC', 'GA', 'FL', 'AL', 'MS', 'AR', 'LA']),
('Midwest', 'Midwest region', ARRAY['OH', 'MI', 'IN', 'WI', 'IL', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS']),
('Southwest', 'Southwest region', ARRAY['TX', 'OK', 'NM', 'AZ']),
('West', 'West region', ARRAY['CO', 'WY', 'MT', 'ID', 'WA', 'OR', 'UT', 'NV', 'CA', 'AK', 'HI']);

-- Default recycling rules
INSERT INTO recycling_rules (name, priority_levels, days_without_contact, min_contact_attempts) VALUES
('High Priority Recycling', ARRAY['A+', 'A'], 7, 3),
('Standard Recycling', ARRAY['B+', 'B', 'C'], 10, 2);

-- Default badges
INSERT INTO badges (name, description, icon, points_required, conditions) VALUES
('First Contact', 'Made your first contact with a lead', 'phone', 10, '{"activity_type": "call", "min_count": 1}'),
('Speed Demon', 'Contacted a lead within 1 hour of assignment', 'lightning', 50, '{"response_time_hours": 1}'),
('Closer', 'Closed 3 deals in a month', 'trophy', 500, '{"deals_closed": 3, "period": "month"}'),
('Lead Hunter', 'Contacted 50 leads in a week', 'target', 250, '{"calls_made": 50, "period": "week"}'),
('Territory King', 'Top performer in territory for the month', 'crown', 1000, '{"rank": 1, "scope": "territory", "period": "month"}');

-- Default system settings
INSERT INTO system_settings (key, value, description) VALUES
('recycling_enabled', 'true', 'Enable automatic lead recycling'),
('recycling_days', '7', 'Days before lead becomes eligible for recycling'),
('min_contact_attempts', '3', 'Minimum contact attempts before recycling'),
('gamification_enabled', 'true', 'Enable gamification features'),
('real_time_notifications', 'true', 'Enable real-time notifications'),
('lead_assignment_algorithm', 'round_robin', 'Algorithm for assigning new leads');

-- ===================================================================
-- VIEWS FOR REPORTING
-- ===================================================================

-- Active leads view
CREATE VIEW active_leads AS
SELECT 
    l.*,
    u.first_name || ' ' || u.last_name AS assigned_agent_name,
    t.name AS territory_name,
    CASE 
        WHEN l.recycling_eligible_at <= NOW() THEN true 
        ELSE false 
    END AS is_eligible_for_recycling
FROM leads l
LEFT JOIN users u ON l.assigned_to = u.id
LEFT JOIN territories t ON l.territory_id = t.id
WHERE l.status NOT IN ('closed_won', 'closed_lost');

-- Performance dashboard view
CREATE VIEW performance_dashboard AS
SELECT 
    u.id AS user_id,
    u.first_name || ' ' || u.last_name AS agent_name,
    COUNT(l.id) AS total_leads,
    COUNT(CASE WHEN l.status = 'qualified' THEN 1 END) AS qualified_leads,
    COUNT(CASE WHEN l.status = 'closed_won' THEN 1 END) AS closed_deals,
    SUM(l.estimated_deal_value) FILTER (WHERE l.status = 'closed_won') AS total_revenue,
    AVG(EXTRACT(EPOCH FROM (l.first_contacted_at - l.assigned_at))/3600) AS avg_response_time_hours
FROM users u
LEFT JOIN leads l ON u.id = l.assigned_to
WHERE u.role = 'agent' AND u.status = 'active'
GROUP BY u.id, u.first_name, u.last_name;

-- Daily leaderboard view
CREATE VIEW daily_leaderboard AS
SELECT 
    le.*,
    u.first_name || ' ' || u.last_name AS agent_name,
    RANK() OVER (PARTITION BY le.date ORDER BY le.total_points DESC) AS daily_rank
FROM leaderboard_entries le
JOIN users u ON le.user_id = u.id
WHERE le.date = CURRENT_DATE;

-- Comments for documentation
COMMENT ON TABLE leads IS 'Enhanced leads table preserving original NPPES scoring system with CRM functionality';
COMMENT ON COLUMN leads.search_vector IS 'Full-text search vector for fast lead searching';
COMMENT ON COLUMN leads.recycling_eligible_at IS 'Timestamp when lead becomes eligible for recycling (7 days after assignment)';
COMMENT ON TABLE gamification IS 'Comprehensive gamification system for sales team motivation'; 