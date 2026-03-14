from flask import render_template,request,redirect,url_for,request,abort
from flask_login import login_user,logout_user,login_required,current_user
from app.models import URLMapping, Click, User
from datetime import datetime
from user_agents import parse
from sqlalchemy import func

def register_routes(app,db,bcrypt,limiter):

    @app.route('/', methods=['GET', 'POST'])
    def index():
        if current_user.is_anonymous:
            return render_template('index.html')
        else:
            url_count=URLMapping.query.filter_by(user_id=current_user.id).count()
            total_short=URLMapping.query.filter_by(user_id=current_user.id).count()
            active_urls=URLMapping.query.filter_by(is_active=True, user_id=current_user.id).count()
            return render_template('index.html', user=current_user, url_count=url_count, total_short=total_short, active_urls=active_urls)

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
            if username == "admin":
                return "Username 'admin' is reserved Use a different username", 400
            else:
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
        custom_code = request.form.get('custom_code')
        is_private = request.form.get('is_private') == 'on'

        if not original_url:
            return "Original URL is required", 400
        
        existing = URLMapping.query.filter_by(original_url=original_url, user_id=current_user.id).first()
        if existing and not custom_code:
            return redirect(url_for('url_dashboard'))
        
        if custom_code:
            if URLMapping.query.filter_by(short_code=custom_code).first():
                return "Custom code already in use", 400
            short_code = custom_code
        else:
            import string,random
            def generate_short_code(length=6):
                characters = string.ascii_letters + string.digits
                return ''.join(random.choice(characters) for _ in range(length))

            short_code = generate_short_code()  

            while URLMapping.query.filter_by(short_code=short_code).first() is not None:
                short_code = generate_short_code()
        
        new_mapping = URLMapping(original_url=original_url, short_code=short_code, user_id=current_user.id, is_private=is_private)
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
        
        import json
        import urllib.request
        import ipaddress
        
        # Get real IP, handling Docker/proxy networks
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
        elif request.headers.get("X-Real-IP"):
            ip = request.headers.get("X-Real-IP")
        else:
            ip = request.remote_addr

        country = request.headers.get('X-Country', 'Unknown')
        region = 'Unknown'
        city = 'Unknown'
        
        # Check if the IP is a private/local network IP (like 127.0.0.1 or 172.20.0.x from Docker)
        is_private = False
        try:
            is_private = ipaddress.ip_address(ip).is_private
        except ValueError:
            pass

        if country == 'Unknown':
            try:
                # If local/private, let ip-api resolve the machine's public IP natively.
                api_url = "http://ip-api.com/json/" if is_private else f"http://ip-api.com/json/{ip}"
                req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
                
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = json.loads(response.read().decode())
                    if data.get('status') == 'success':
                        country = data.get('country', 'Unknown')
                        region = data.get('regionName', 'Unknown')
                        city = data.get('city', 'Unknown')
                            
            except Exception as e:
                print(e)
                pass

        new_click = Click(
            url_mapping_id=url.id,
            user_agent=request.headers.get('User-Agent'),
            ip_address=ip,
            referrer=request.referrer,
            country=country,
            region=region,
            city=city,
            browser=ua.browser.family,
            os=ua.os.family,
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

        devices = (
            db.session.query(
            Click.device_type, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.device_type).all()
        )
        
        browsers = (
            db.session.query(
            Click.browser, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.browser).all()
        )

        countries = (
            db.session.query(
            Click.country, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.country).all()
        )

        regions = (
            db.session.query(
            Click.region, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.region).all()
        )

        cities = (
            db.session.query(
            Click.city, func.count(Click.id)
        ).filter_by(url_mapping_id=url.id).group_by(Click.city).all()
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
                               devices=devices,
                               browsers=browsers,
                               countries=countries,
                               regions=regions,
                               cities=cities,
                               referrer_stats=referrer_stats)

