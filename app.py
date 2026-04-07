import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Product, Cart, Order, OrderItem  # ✅ FIXED IMPORT

app = Flask(__name__)
app.config.from_object(Config)

# ==============================
# IMAGE UPLOAD FOLDER
# ==============================

UPLOAD_FOLDER = "static/product_images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth"
login_manager.login_message = ""
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==============================
# HOME PAGE
# ==============================

@app.route("/")
def index():
    return render_template("index.html")


# ==============================
# AUTH PAGE
# ==============================

@app.route("/auth")
def auth():
    return render_template("auth.html")


# ==============================
# REGISTER
# ==============================

@app.route("/register", methods=["POST"])
def register():
    user = User(
        name=request.form["name"],
        password=generate_password_hash(request.form["password"]),
        address=request.form["address"],
        contact=request.form["contact"],
        role=request.form["role"]
    )

    db.session.add(user)
    db.session.commit()

    return redirect(url_for("auth"))


# ==============================
# LOGIN
# ==============================

from flask import flash

@app.route("/login", methods=["POST"])
def login():

    name = request.form["name"]   
    password = request.form["password"]

    user = User.query.filter_by(name=name).first()

    if user and check_password_hash(user.password, password):
    
        login_user(user)

        if user.role == "farmer":
            return redirect(url_for("farmer_dashboard"))

        return redirect(url_for("marketplace"))

    # ❌ WRONG LOGIN
    flash("Invalid username or password ❌")  
    return redirect(url_for("auth"))  


# ==============================
# FARMER DASHBOARD
# ==============================

@app.route("/farmer_dashboard", methods=["GET", "POST"])
@login_required
def farmer_dashboard():

    if current_user.role != "farmer":
        return redirect(url_for("index"))

    if request.method == "POST":

        image_file = request.files["image"]
        filename = None

        if image_file and image_file.filename != "":
            filename = str(uuid.uuid4()) + "_" + secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        product = Product(
            name=request.form["name"],
            price=request.form["price"],
            description=request.form["description"],
            category=request.form["category"],
            image=filename,
            farmer_id=current_user.id
        )

        db.session.add(product)
        db.session.commit()

    products = Product.query.filter_by(farmer_id=current_user.id).all()

    return render_template("farmer_dashboard.html", products=products)


# ==============================
# MARKETPLACE
# ==============================

@app.route("/marketplace")
@login_required
def marketplace():

    products = Product.query.all()
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    cart_count = sum(item.quantity for item in cart_items)

    return render_template(
        "marketplace.html",
        products=products,
        cart_items=cart_items,
        cart_count=cart_count
    )


# ==============================
# CATEGORY
# ==============================

@app.route("/category/<category_name>")
@login_required
def category(category_name):

    products = Product.query.filter_by(category=category_name).all()
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    cart_count = sum(item.quantity for item in cart_items)

    return render_template(
        "marketplace.html",
        products=products,
        cart_items=cart_items,
        cart_count=cart_count
    )


# ==============================
# ADD TO CART
# ==============================

@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):

    item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if item:
        item.quantity += 1
    else:
        item = Cart(user_id=current_user.id, product_id=product_id, quantity=1)
        db.session.add(item)

    db.session.commit()

    return redirect(request.referrer)


# ==============================
# DECREASE CART
# ==============================

@app.route("/decrease_cart/<int:product_id>")
@login_required
def decrease_cart(product_id):

    item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()

    if item:
        item.quantity -= 1
        if item.quantity <= 0:
            db.session.delete(item)

    db.session.commit()

    return redirect(request.referrer)


# ==============================
# CART PAGE (UPDATED)
# ==============================

@app.route("/cart")
@login_required
def cart():

    items = db.session.query(Cart, Product)\
        .join(Product, Cart.product_id == Product.id)\
        .filter(Cart.user_id == current_user.id).all()

    total = sum(item.Cart.quantity * item.Product.price for item in items)

    delivery_charge = 0 if total >= 800 else 50
    grand_total = total + delivery_charge

    return render_template(
        "cart.html",
        items=items,
        total=total,
        delivery_charge=delivery_charge,
        grand_total=grand_total
    )


# ==============================
# CHECKOUT
# ==============================

@app.route("/checkout")
@login_required
def checkout():

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()

    total = 0
    for item in cart_items:
        product = Product.query.get(item.product_id)
        total += product.price * item.quantity

    # create order
    order = Order(user_id=current_user.id, total_price=total)
    db.session.add(order)
    db.session.commit()

    # add items
    for item in cart_items:
        db.session.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantity=item.quantity
        ))

    # clear cart
    Cart.query.filter_by(user_id=current_user.id).delete()

    db.session.commit()

    return redirect("/orders")


# ==============================
# ORDERS PAGE
# ==============================

@app.route("/orders")
@login_required
def orders():

    orders = Order.query.filter_by(user_id=current_user.id).all()

    return render_template("orders.html", orders=orders)


# ==============================
# PRODUCT DETAILS
# ==============================

@app.route("/product/<int:id>")
def product_detail(id):

    product = Product.query.get(id)

    return render_template("product_detail.html", product=product)


# ==============================
# DELETE PRODUCT
# ==============================

@app.route("/delete_product/<int:id>")
def delete_product(id):

    product = Product.query.get(id)
    db.session.delete(product)
    db.session.commit()

    return redirect("/farmer_dashboard")


# ==============================
# SEARCH
# ==============================

@app.route("/search")
@login_required
def search():

    query = request.args.get("q")

    products = Product.query.filter(Product.name.contains(query)).all()

    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    cart_count = sum(item.quantity for item in cart_items)

    return render_template(
        "marketplace.html",
        products=products,
        cart_items=cart_items,
        cart_count=cart_count
    )


# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


# ==============================
# DEV LOGIN
# ==============================

@app.route("/devlogin")
def devlogin():

    user = User.query.first()
    if user:
        login_user(user)

    return redirect("/marketplace")


# ==============================
# RUN
# ==============================

if __name__ == "__main__":

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    with app.app_context():
        db.create_all()

    app.run(debug=True)