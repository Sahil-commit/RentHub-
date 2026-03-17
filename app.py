import os
import secrets
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from config import Config
from models import db, User, Item, Rental, ContactMessage, Review
from forms import RegistrationForm, LoginForm, ItemForm, ContactForm, EditBankDetailsForm, ReviewForm

app = Flask(__name__)
app.config.from_object(Config)

import stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], picture_fn)
    
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        
    form_picture.save(picture_path)
    return picture_fn

@app.route("/")
def home():
    featured_items = Item.query.filter_by(is_available=True).order_by(Item.created_at.desc()).limit(6).all()
    categories = ['Electronics', 'Vehicles', 'Tools', 'Party Supplies', 'Other']
    return render_template('index.html', featured_items=featured_items, categories=categories)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(name=form.name.data, email=form.email.data, message=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            address=form.address.data,
            bank_name=form.bank_name.data,
            account_holder_name=form.account_holder_name.data,
            account_number=form.account_number.data,
            ifsc_code=form.ifsc_code.data,
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data) and not user.is_admin:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/dashboard", methods=['GET', 'POST'])
@login_required
def dashboard():
    bank_form = EditBankDetailsForm()
    if bank_form.validate_on_submit():
        current_user.bank_name = bank_form.bank_name.data
        current_user.account_holder_name = bank_form.account_holder_name.data
        current_user.account_number = bank_form.account_number.data
        current_user.ifsc_code = bank_form.ifsc_code.data
        db.session.commit()
        flash('Bank details updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        bank_form.bank_name.data = current_user.bank_name
        bank_form.account_holder_name.data = current_user.account_holder_name
        bank_form.account_number.data = current_user.account_number
        bank_form.ifsc_code.data = current_user.ifsc_code
        
    my_items = Item.query.filter_by(user_id=current_user.id).all()
    my_rentals = Rental.query.filter_by(user_id=current_user.id).all()
    pending_requests = []
    earnings = 0
    rented_out = []
    for item in my_items:
        for r in item.rentals:
            if r.status == 'Pending':
                pending_requests.append(r)
            elif r.status in ['Active', 'Completed']:
                earnings += r.total_price
                rented_out.append(r)
            
    return render_template('dashboard.html', bank_form=bank_form, items=my_items, rentals=my_rentals, earnings=earnings, rented_out=rented_out, pending_requests=pending_requests)

@app.route("/add-item", methods=['GET', 'POST'])
@login_required
def add_item():
    form = ItemForm()
    if form.validate_on_submit():
        picture_file = save_picture(form.image.data) if form.image.data else None
        item = Item(
            name=form.name.data,
            description=form.description.data,
            category=form.category.data,
            rental_price=form.rental_price.data,
            image_filename=picture_file,
            is_available=form.is_available.data,
            owner=current_user
        )
        db.session.add(item)
        db.session.commit()
        flash('Your item has been listed!', 'success')
        return redirect(url_for('items'))
    return render_template('add_item.html', form=form)

@app.route("/items")
def items():
    q = request.args.get('q', '')
    category = request.args.get('category', '')
    
    query = Item.query.filter_by(is_available=True)
    if q:
        query = query.filter(Item.name.ilike(f'%{q}%'))
    if category and category != 'All':
        query = query.filter(Item.category.ilike(category))
        
    items_list = query.order_by(Item.created_at.desc()).all()
    # Unique categories
    categories = ['All'] + [c[0].capitalize() for c in db.session.query(Item.category).distinct()]
    return render_template('items.html', items=items_list, categories=categories, current_category=category.capitalize() if category else 'All')

@app.route("/item/<int:item_id>", methods=['GET', 'POST'])
def item_detail(item_id):
    item = Item.query.get_or_404(item_id)
    review_form = ReviewForm()
    
    # Fetch up to 3 other available items (prefer same category, but use any available items to fill up to 3)
    related_items = Item.query.filter(Item.category == item.category, Item.id != item.id, Item.is_available == True).order_by(Item.created_at.desc()).limit(3).all()
    
    if len(related_items) < 3:
        exclude_ids = [item.id] + [ri.id for ri in related_items]
        needed = 3 - len(related_items)
        other_items = Item.query.filter(~Item.id.in_(exclude_ids), Item.is_available == True).order_by(Item.created_at.desc()).limit(needed).all()
        related_items.extend(other_items)

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('You must be logged in to perform this action.', 'warning')
            return redirect(url_for('login', next=request.url))
        
        action = request.form.get('action')
        
        if action == 'rent':
            days = int(request.form.get('days', 1))
            rental = Rental(
                item=item, 
                renter=current_user, 
                total_price=item.rental_price * days,
                status='Pending'
            )
            db.session.add(rental)
            db.session.commit()
            flash('Your rental request has been sent to the owner for approval.', 'success')
            return redirect(url_for('my_rentals'))
            
        elif action == 'review' and review_form.validate_on_submit():
            # Add or update review
            existing_review = Review.query.filter_by(item_id=item.id, user_id=current_user.id).first()
            if existing_review:
                existing_review.rating = int(review_form.rating.data)
                existing_review.comment = review_form.comment.data
                flash('Your review has been updated.', 'info')
            else:
                review = Review(item=item, user=current_user, rating=int(review_form.rating.data), comment=review_form.comment.data)
                db.session.add(review)
                flash('Your review has been submitted.', 'success')
            db.session.commit()
            return redirect(url_for('item_detail', item_id=item.id))
        
    return render_template('item_detail_v2.html', item=item, review_form=review_form, related_items=related_items)

@app.route("/item/<int:item_id>/delete", methods=['POST'])
@login_required
def delete_user_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    for rental in item.rentals:
        db.session.delete(rental)
    for review in item.reviews:
        db.session.delete(review)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('dashboard'))

@app.route("/item/<int:item_id>/toggle", methods=['POST'])
@login_required
def toggle_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    item.is_available = not item.is_available
    db.session.commit()
    status_str = "Available" if item.is_available else "Unavailable"
    flash(f'Item marked as {status_str}.', 'success')
    return redirect(url_for('dashboard'))

@app.route("/rental/<int:rental_id>/approve", methods=['POST'])
@login_required
def approve_rental(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.item.user_id != current_user.id:
        abort(403)
    rental.status = 'Approved'
    db.session.commit()
    flash('Rental request approved. The user can now pay for it.', 'success')
    return redirect(url_for('dashboard'))

@app.route("/rental/<int:rental_id>/reject", methods=['POST'])
@login_required
def reject_rental(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.item.user_id != current_user.id:
        abort(403)
    rental.status = 'Rejected'
    db.session.commit()
    flash('Rental request rejected.', 'info')
    return redirect(url_for('dashboard'))

@app.route("/checkout/<int:rental_id>")
@login_required
def checkout(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.user_id != current_user.id or rental.status != 'Approved':
        abort(403)
        
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f"Rental Checkout: {rental.item.name}",
                    },
                    'unit_amount': int(rental.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', rental_id=rental.id, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('my_rentals', _external=True),
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('my_rentals'))

@app.route("/payment-success/<int:rental_id>")
@login_required
def payment_success(rental_id):
    session_id = request.args.get('session_id')
    if not session_id:
        return redirect(url_for('home'))
        
    rental = Rental.query.get_or_404(rental_id)
    if rental.user_id != current_user.id:
        abort(403)
        
    try:
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        if checkout_session.payment_status != 'paid':
            flash('Payment not completed.', 'warning')
            return redirect(url_for('my_rentals'))
    except Exception as e:
        flash('Invalid session.', 'danger')
        return redirect(url_for('my_rentals'))
        
    rental.status = 'Active'
    rental.item.is_available = False # Mark as actively rented
    db.session.commit()
    flash('Payment successful! Your rental is now Active.', 'success')
    return redirect(url_for('my_rentals'))

@app.route("/my-rentals")
@login_required
def my_rentals():
    rentals = Rental.query.filter_by(user_id=current_user.id).order_by(Rental.rental_date.desc()).all()
    return render_template('my_rentals.html', rentals=rentals)

# Admin Routes
@app.route("/admin/login", methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_admin and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Admin login failed. Invalid credentials.', 'danger')
    return render_template('admin/login.html', form=form)

@app.route("/admin")
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        abort(403)
    total_users = User.query.filter_by(is_admin=False).count()
    total_items = Item.query.count()
    total_rentals = Rental.query.count()
    total_revenue = db.session.query(db.func.sum(Rental.total_price)).scalar() or 0.0
    return render_template('admin/dashboard.html', total_users=total_users, total_items=total_items, 
                           total_rentals=total_rentals, total_revenue=total_revenue)

@app.route("/admin/users")
@login_required
def admin_users():
    if not current_user.is_admin:
        abort(403)
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route("/admin/user/<int:user_id>/delete", methods=['POST'])
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        abort(403)
    user = User.query.get_or_404(user_id)
    # Cascading manually if sqlite or no cascade defined
    for item in user.items:
        for rental in item.rentals:
            db.session.delete(rental)
        for review in item.reviews:
            db.session.delete(review)
        db.session.delete(item)
    for rental in user.rentals:
        db.session.delete(rental)
    for review in user.reviews:
        db.session.delete(review)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route("/admin/items")
@login_required
def admin_items():
    if not current_user.is_admin:
        abort(403)
    items = Item.query.all()
    return render_template('admin/items.html', items=items)

@app.route("/admin/item/<int:item_id>/delete", methods=['POST'])
@login_required
def delete_item(item_id):
    if not current_user.is_admin:
        abort(403)
    item = Item.query.get_or_404(item_id)
    # delete associated rentals
    for rental in item.rentals:
        db.session.delete(rental)
    for review in item.reviews:
        db.session.delete(review)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted successfully.', 'success')
    return redirect(url_for('admin_items'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(is_admin=True).first():
            hashed_pw = bcrypt.generate_password_hash("admin").decode('utf-8')
            admin = User(
                full_name="Admin",
                email="admin@renthub.com",
                phone_number="0000000000",
                address="Admin HQ",
                bank_name="Admin Bank",
                account_holder_name="Admin",
                account_number="00000",
                ifsc_code="00000",
                password=hashed_pw,
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True)
