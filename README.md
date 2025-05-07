# pet-adoption-site


🐾 Pet Adoption Website
It is my first site that include every feature required for a basic website. This is my project in first year. I have deployed this site on pythonanywhere.com and you can take a look to it. 

https://sourabhbansal.pythonanywhere.com/

The site is completly responsive for mobile phone and desktops.

 A full-featured pet adoption platform built with Django, allowing users to view adoptable pets, submit adoption requests, manage blog posts, and handle contact/letter submissions. It includes role-based access with Superadmin and Staff Admin views.


Home page
![home page](readmeimages/image.png)

Contact us page 
![contact us page](readmeimages/image-1.png)
![contact us page ](readmeimages/image-5.png)

profile page 
![profile page ](readmeimages/image-2.png)
![profile page](readmeimages/image-3.png)
![sprofile page](readmeimages/image-4.png)

Blog page 
![blog page](readmeimages/image-6.png)
![blog page](readmeimages/image-7.png)

Shop 
![store](readmeimages/image-8.png)
![store](readmeimages/image-9.png)   

my cart
![my cart](readmeimages/image-10.png)

after checkout 
![checkout](readmeimages/image-11.png)

my orders
![my orders](readmeimages/image-12.png)

invoice pdf 
![invoice](readmeimages/image-13.png)

email after checkout
![alt text](readmeimages/<WhatsApp Image 2025-05-08 at 01.43.26_8f2a70cd.jpg>)

admin pannel
![alt text](readmeimages/image-14.png)
![alt text](readmeimages/image-15.png)
![alt text](readmeimages/image-16.png)
![alt text](readmeimages/image-17.png)





🚀 Setup Instructions
bash
Copy
Edit
https://github.com/sourabhbansal111/pet-adoption-site.git
cd petadoption
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
📁 Folder Structure
csharp
Copy
Edit
petadoption/
│
├── home/                 # Main Django app
├── static/
│   └── images/
│       └── uploads/      # Uploaded pet/blog images
│       └── screenshots/  # Screenshots for README
├── templates/
│   └── home/
│       └── *.html        # All HTML templates
├── manage.py
└── README.md
📌 Technologies Used


Django

SQLite (default)

HTML/CSS (Internal styling)

Bootstrap (optional, minimal)

Email backend (for OTP)

JavaScript (minimal or none, based on use)

Let me know if you want me to generate placeholder screenshots for each section or help you format them in your actual project folder. Would you like me to do that?
