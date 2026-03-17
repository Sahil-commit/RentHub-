import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-for-renthub'
    
    # Try MySQL first (XAMPP default), fallback to SQLite if XAMPP is off
    try:
        import pymysql
        pymysql.connect(host='localhost', user='root', password='')
        db_url = 'mysql+pymysql://root:@localhost/renthub'
    except Exception:
        db_url = 'sqlite:///' + os.path.join(BASE_DIR, 'renthub.db')

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY') or 'pk_test_51SzUSGGyqXNt9gySpjK3HAO3IY8EQMNxKZwkik53aRhzpDBFRNDdhu0bo0nd4DOiO26GSYGVcd4koStvDjpEFFq400aC2fq0y5' # replace with yours
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_51SzUSGGyqXNt9gySF35yE2s9OOdwwW1fjqbZplboHZjuugvP53kWdZvCxLXR3C9f8bJfkYNt4VDkgzUp8EFYh4nG002tvTZJBu' # replace with yours
