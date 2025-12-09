from flask import Flask, request, render_template
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# load files===========================================================================================================
trending_products = pd.read_csv("C:\\vs_code_sk\\Ecommerce_Product_recommendation_system\\E-Commerece-Recommendation-System-Machine-Learning-Product-Recommendation-system-\\models\\trending_products.csv")
train_data = pd.read_csv("C:\\vs_code_sk\\Ecommerce_Product_recommendation_system\\E-Commerece-Recommendation-System-Machine-Learning-Product-Recommendation-system-\\models\\clean_data.csv")

# database configuration---------------------------------------
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/ecom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define your model class for the 'signup' table
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define your model class for the 'signin' table
class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Recommendations functions============================================================================================
# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text


def content_based_recommendations(train_data, item_name, top_n=10):
    # 1) Try to find closest match (case-insensitive, partial)
    matches = train_data[train_data['Name'].str.contains(item_name, case=False, na=False)]

    if matches.empty:
        print(f"Item '{item_name}' not found in the training data.")
        return pd.DataFrame()

    # 2) Use first matched product as the reference item
    actual_name = matches.iloc[0]['Name']
    print(f"Using matched product name: {actual_name}")

    # Create a TF-IDF vectorizer for item descriptions
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    # Apply TF-IDF vectorization to item descriptions
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])

    # Calculate cosine similarity between items based on descriptions
    cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

    # Find the index of the item
    item_index = train_data[train_data['Name'] == actual_name].index[0]

    # Get the cosine similarity scores for the item
    similar_items = list(enumerate(cosine_similarities_content[item_index]))

    # Sort similar items by similarity score in descending order
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)

    # Get the top N most similar items (excluding the item itself)
    top_similar_items = similar_items[1:top_n+1]

    # Get the indices of the top similar items
    recommended_item_indices = [x[0] for x in top_similar_items]

    # Get the details of the top similar items
    recommended_items_details = train_data.iloc[recommended_item_indices][
        ['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']
    ]

    return recommended_items_details

# routes===============================================================================
# List of predefined image URLs
random_image_urls = [
    "static/img/img_1.png",
    "static/img/img_2.png",
    "static/img/img_3.png",
    "static/img/img_4.png",
    "static/img/img_5.png",
    "static/img/img_6.png",
    "static/img/img_7.png",
    "static/img/img_8.png",
]


@app.route("/")
def index():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html',trending_products=trending_products.head(8),truncate = truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price = random.choice(price))

@app.route("/main")
def main():
    return render_template(
        "main.html",
        content_based_rec=None,
        message=None,
        random_price=None,
        truncate=truncate
    )


# routes
@app.route("/index")
def indexredirect():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random.choice(price))

@app.route("/signup", methods=['POST','GET'])
def signup():
    if request.method=='POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

        # Create a list of random image URLs for each product
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price),
                               signup_message='User signed up successfully!'
                               )

# Route for signup page
@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']

        # 1) Check user exists in Signup table (REAL verification)
        user = Signup.query.filter_by(username=username, password=password).first()

        # Create a list of random image URLs for each product
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        if user:
            # Optional: also log signin activity
            signin_log = Signin(username=username, password=password)
            db.session.add(signin_log)
            db.session.commit()

            message = "User signed in successfully!"
        else:
            message = "Invalid username or password."

        return render_template(
            'index.html',
            trending_products=trending_products.head(8),
            truncate=truncate,
            random_product_image_urls=random_product_image_urls,
            random_price=random.choice(price),
            signup_message=message
        )

    # GET request -> just show home page
    return index()

@app.route("/recommendations", methods=["GET", "POST"])
def recommendations():
    # Agar kisi ne /recommendations ko direct URL se open kiya (GET request)
    # toh simply empty main page dikha do
    if request.method == "GET":
        return render_template(
            "main.html",
            content_based_rec=None,
            message=None,
            random_price=None
        )

    # Yahan se POST (form submit) handle hoga
    prod = request.form.get("prod", "").strip()
    nbr_raw = request.form.get("nbr", "").strip()

    message = None
    content_based_rec = None

    # 1) Agar user ne product naam hi nahi dala
    if not prod:
        message = "Please enter a product name."
    else:
        # 2) Number of recommendations ko safely handle karo
        try:
            # agar user ne kuch nahi dala toh default 10
            nbr = int(nbr_raw) if nbr_raw else 10
            if nbr <= 0:
                nbr = 10
        except ValueError:
            # agar user ne galat value daali (jaise 'abc') toh bhi 10
            nbr = 10

        # 3) Model se recommendations laao
        content_based_rec = content_based_recommendations(
            train_data,
            prod,
            top_n=nbr
        )

        # 4) Agar kuch mila hi nahi
        if content_based_rec.empty:
            message = "No recommendations available for this product."
            content_based_rec = None
        else:
            message = f"Showing {len(content_based_rec)} recommendations for '{prod}'."

    # 5) Random price list (jaisa tum pehle use kar rahe the)
    price_list = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

    # 6) Hamesha main.html ko ye sab variables ke sath bhejo
    return render_template(
        "main.html",
        content_based_rec=content_based_rec,  # DataFrame ya None
        truncate=truncate,                    # name chhota karne ka function
        message=message,                      # user ko dikhne wala text
        random_price=random.choice(price_list)
    )



if __name__=='__main__':
    app.run(debug=True)