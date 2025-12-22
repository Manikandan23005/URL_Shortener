from flask import render_template,request,redirect,url_for,request,abort
from flask_login import login_user,logout_user,login_required,current_user
from app.models import URLMapping, Click, User
from datetime import datetime
from user_agents import parse
from sqlalchemy import func

def register_routes(app,db,bcrypt,limiter):

    @app.route('/', methods=['GET', 'POST'])
    def index():
        url_count=URLMapping.query.count()
        total_clicks=Click.query.count()
        active_urls=URLMapping.query.filter_by(is_active=True).count()
        return render_template('index.html', user=current_user, url_count=url_count, total_clicks=total_clicks, active_urls=active_urls)

    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("5 per minute")
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('index'))
            else:
                return "Invalid credentials", 401

    @app.route('/signup', methods=['GET', 'POST'])
    @limiter.limit("3 per minute")
    def signup():
        if request.method == 'GET':
            return render_template('signup.html')
        elif request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            mail = request.form.get('email')
            hashed_password = bcrypt.generate_password_hash(password)
            new_user = User(username=username, password=hashed_password, email=mail)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('index'))
        
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/url_dashboard')
    @login_required
    def url_dashboard():
        url_mappings = URLMapping.query.filter_by(user_id=current_user.id).all()
        return render_template('URL_Dashboard.html', url_mappings=url_mappings)

    @app.route('/shorten', methods=['POST'])
    @login_required
    @limiter.limit("10 per minute")
    def shorten_url():

        original_url = request.form.get('original_url')
        if not original_url:
            return "Original URL is required", 400
        
        existing = URLMapping.query.filter_by(original_url=original_url, user_id=current_user.id).first()
        if existing:
            return redirect(url_for('url_dashboard'))
        
        import string,random
        def generate_short_code(length=6):
            characters = string.ascii_letters + string.digits
            return ''.join(random.choice(characters) for _ in range(length))

        short_code = generate_short_code()  

        while URLMapping.query.filter_by(short_code=short_code).first() is not None:
            short_code = generate_short_code()
        
        new_mapping = URLMapping(original_url=original_url, short_code=short_code, user_id=current_user.id)
        db.session.add(new_mapping)
        db.session.commit()
        return redirect(url_for('url_dashboard'))
    
    @app.route('/<short_code>')
    @limiter.limit("60 per minute")
    def redirect_short_url(short_code):

        url=URLMapping.query.filter_by(short_code=short_code, is_active=True).first()
        if url is None:
            return abort(404)
        
        if url.expires_at and url.expires_at < datetime.now(datetime.UTC):
            return abort(404)
        
        if url.max_clicks is not None:
            click_count = Click.query.filter_by(url_mapping_id=url.id).count()
            if click_count >= url.max_clicks:
                return abort(404)
            
        if url.is_private:
            if not current_user.is_authenticated:
                return abort(403)
            if not current_user.is_admin() and current_user.id != url.user_id:
                return abort(403)
            
        if len(request.headers.get('User-Agent', '')) <10:
            abort(403)
        ua_string = request.headers.get('User-Agent', '')
        ua = parse(ua_string)
        browser = ua.browser.family
        os = ua.os.family   
        
        new_click = Click(
            url_mapping_id=url.id,
            user_agent=f"{browser} on {os}",
            ip_address=request.remote_addr,
            referrer=request.referrer,
            country=request.headers.get('X-Country', 'Unknown'),
            device_type='Mobile' if ua.is_mobile else 'Tablet' if ua.is_tablet else 'PC' if ua.is_pc else 'Bot' if ua.is_bot else 'Other'
        )

        try:
            db.session.add(new_click)
            db.session.commit()
        except Exception:
            db.session.rollback()
            
        return redirect(url.original_url, code=url.redirect_type)

    @app.route('/analytics/<short_code>')
    @login_required
    def analytics(short_code):
        url = URLMapping.query.filter_by(short_code=short_code).first_or_404()
        if url.user_id != current_user.id:
            return abort(403)
        
        total_clicks = Click.query.filter_by(url_mapping_id=url.id).count()

        clicks_over_time = (
            db.session.query(
            func.date(Click.click_time),func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(func.date(Click.click_time)).all()
        )

        country_stats = (
            db.session.query(
            Click.country, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.country).all()
        )
        
        user_agent = (
            db.session.query(
            Click.user_agent, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.user_agent).all()
        )   

        referrer_stats = (
            db.session.query(
            Click.referrer, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.referrer).all()
        )
        
        return render_template('analytics.html', 
                               url=url, 
                               total_clicks=total_clicks,
                               clicks_over_time=clicks_over_time, 
                               country_stats=country_stats,
                               user_agent=user_agent,
                               referrer_stats=referrer_stats)

