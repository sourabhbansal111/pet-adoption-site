from django.contrib import messages
from django.contrib.auth import authenticate,login,logout

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Usert,Blog
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.db.models import Q

from django.http import HttpResponse

from django.core.mail import send_mail
import os
from django.http import JsonResponse
import json

import random
from .forms import UserUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

from django.views.decorators.http import require_POST
import requests
from django.shortcuts import render, redirect # Removed get_object_or_404, Http404 as they are not used in this version
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse # Useful for redirects
from django.conf import settings

FLASK_API_URL = "http://127.0.0.1:5001" # Adjust if your Flask app runs elsewhere

# Create your views here.
def home(request):
    return render(request ,'home.html')

def aboutus(request):
    return render(request ,'about.html')

# === Role check decorators ===
def is_admin(user):
    return user.role == "admin"

def is_superadmin(user):
    return user.role == "superadmin"

# === Auth Views ===

def register_view(request):
    if request.method=="POST":
        name=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')
        cpassword=request.POST.get('cpassword')
        if request.POST.get('role'): 
            if not name:
                messages.error(request,"please enter valid username")
            elif password!=cpassword:
                messages.error(request,"password not match")
            elif Usert.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
            elif Usert.objects.filter(username=name).exists():
                messages.error(request, "Username already taken.")
            else:
                Usert.objects.create(
                username=name,
                email=email,
                password=password,
                is_staff=True
                )
                messages.success(request,"registered successfuly")
            return redirect('adminpage')
        if not name:
            messages.error(request,"please enter valid username")
        elif password!=cpassword:
            messages.error(request,"password not match")
        elif Usert.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
        elif Usert.objects.filter(username=name).exists():
            messages.error(request, "Username already taken.")
        else:
            Usert.objects.create_user(
                username=name,
                email=email,
                password=password,
            )
            messages.success(request,"registered successfuly")
    return render(request,'login.html')

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = None

        # Try with username if given
        if username:
            user = authenticate(request, username=username, password=password)

        # If not authenticated and email is provided, try to find username by email
        if user is None and email:
            try:
                user_obj = Usert.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except Usert.DoesNotExist:
                user = None

        if user:
            login(request, user)
            messages.success(request, "User logged in successfully")
            return redirect('home')
        else:
            messages.error(request, "Invalid credentials. Please check your info.")

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def verifyemail_view(request,email):
    if request.user.email != email:
        raise Http404("You're not allowed to access this page.")

    if request.user.is_verified:
        return render(request,'success.html')
    
    if request.method == "POST":
        if 'send_otp' in request.POST:
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            request.session['otp'] = otp
            request.session['otp_email'] = request.user.email

            send_mail(
                subject = "Your PetCare Email Verification Code",
                message = f"""
Hi { request.user.username},

We received a request to verify your email address for your PetCare account.

Your one-time verification code is: {otp}

Please enter this code on the PetCare website or app to complete your verification. This code will expire in 10 minutes. For your security, do not share this code with anyone.

If you didn’t request this, you can safely ignore this email.

Thanks,  
The PetCare Team  
https://www.petcare.com

PetCare Inc. | 123 Paw Street | New York, NY 10001  
""",

                from_email='parkspaws.petcare@gmail.com',
                recipient_list=[request.user.email],
                 html_message=f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <p>Hi { request.user.username },</p>
    <p>We received a request to change the password for your PetCare account.</p>
    <p>Your one-time verification code is:</p>
    <p style="font-size: 24px; font-weight: bold; color: #2c7be5;">{otp}</p>
    <p>Please enter this code on the PetCare website or app to complete your verification. This code will expire in 10 minutes. For your security, do not share this code with anyone.</p>
    <p>If you didn’t request this, you can safely ignore this email.</p>
    <br>
    <p>Thanks,<br>The PetCare Team</p>
    <p><a href="https://www.petcare.com">https://www.petcare.com</a></p>
    <footer style="font-size: 12px; color: #888;">
      <p>PetCare Inc. | 123 Paw Street | New York, NY 10001</p>
    </footer>
  </body>
</html>
""",
                fail_silently=False,
            )

            messages.success(request, 'OTP sent to your email!')
            return render(request, 'verifyemail.html', {
                'user': request.user,
                'show_otp_form': True
            })

        elif 'verify_otp' in request.POST:
            entered_otp = ''.join([request.POST.get(f'digit{i}', '') for i in range(1, 7)])
            if entered_otp == request.session.get('otp'):
                request.user.is_verified = True
                request.user.save()
                
                send_mail(
                    subject = "Your PetCare Email Verification Code",
                    message = f"""
Hi {request.user.username },

🎉 Your email ({{ request.user.email }}) has been successfully verified.

You're now fully set to enjoy everything PetCare has to offer – from personalized features to secure access.

If this wasn't you or you believe your account was verified by mistake, please contact us immediately.

Thanks for verifying and being part of our community 🐾

Thanks,  
The PetCare Team  
https://www.petcare.com

PetCare Inc. | 123 Paw Street | New York, NY 10001  

""",

                    from_email='parkspaws.petcare@gmail.com',
                    recipient_list=[request.user.email],
                    fail_silently=False,
                )

                messages.success(request, 'Email verified successfully!')
                return redirect('success',email=request.user.email)
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
                return render(request, 'verifyemail.html', {
                    'user': request.user,
                    'show_otp_form': True
                })

    return render(request, 'verifyemail.html', {'user': request.user})


@login_required
def success_view(request,email):
    if email==request.user.email:
        return render(request, 'success.html')  
    else:
        raise Http404("You're not allowed to access this page.")

# === Dashboard ===
def blog(request, blog=""):
    if blog == "adopt":
        blogs = Blog.objects.filter(type='adopt')
    elif blog == "service":
        blogs = Blog.objects.filter(type='service')
    else:
        blogs = Blog.objects.all()

    return render(request, 'blog.html', {'blogs': blogs,'key':blog})



# @login_required
# def profile(request,email):
#     if request.user.email != email:
#         raise Http404("You're not allowed to access this page.")
    
#     form = UserUpdateForm(instance=request.user)
#     user_email = request.user.email
#     contacts = Contact.objects.filter(email=user_email)
#     letters = Letter.objects.filter(email=user_email)
#     conditions = [
#         any(contact.status=="accepted" for contact in Contact.objects.all()),  # Condition 1
#         any(contact.status=="declined" for contact in Contact.objects.all()),  # Condition 2
#         any(contact.status=="pending" for contact in Contact.objects.all()),   # Condition 3
#         any(letter.status=="Viewed" for letter in Letter.objects.all()),       # Condition 4
#         any(letter.status=="Not Viewed" for letter in Letter.objects.all())    # Condition 5
#     ]
#     return render(request, 'profile.html', {'contacts': contacts, 'letters': letters, 'form': form, 'co' : conditions})

@login_required
def profile(request, email):
    """
    Displays user profile information, fetching contacts and letters
    associated with the user's email from the Flask API.
    Also calculates conditions based on all contacts/letters from the API.
    """
    # Security check: Ensure the logged-in user is accessing their own profile
    if request.user.email != email:
        raise Http404("You're not allowed to access this page.")

    # Initialize variables for data fetched from API
    user_contacts = []
    user_letters = []
    all_contacts_api = []
    all_letters_api = []
    conditions = [False] * 5 # Initialize conditions to False

    # Django User form (remains unchanged) - Ensure UserUpdateForm is imported
    # form = UserUpdateForm(instance=request.user)
    form = UserUpdateForm(instance=request.user)
    # Example:
    # try:
    #     from .forms import UserUpdateForm # Make sure to import your form
    #     form = UserUpdateForm(instance=request.user)
    # except ImportError:
    #     messages.warning(request, "UserUpdateForm not found. Profile editing disabled.")
    #     form = None # Ensure form is None if import fails

    user_email = request.user.email

    try:
        # Fetch ALL contacts from Flask API
        contacts_response = requests.get(f"{FLASK_API_URL}/contacts")
        contacts_response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        all_contacts_api = contacts_response.json()

        # Filter contacts for the current user by email
        user_contacts = [c for c in all_contacts_api if c.get('email') == user_email]

        # Fetch ALL letters from Flask API
        letters_response = requests.get(f"{FLASK_API_URL}/letters")
        letters_response.raise_for_status()
        all_letters_api = letters_response.json()

        # Filter letters for the current user by email
        user_letters = [l for l in all_letters_api if l.get('email') == user_email]

        # Calculate conditions based on ALL contacts and letters fetched from API
        conditions = [
            any(contact.get('status') == "accepted" for contact in all_contacts_api),
            any(contact.get('status') == "declined" for contact in all_contacts_api),
            any(contact.get('status') == "pending" for contact in all_contacts_api),
            any(letter.get('status') == "Viewed" for letter in all_letters_api),
            any(letter.get('status') == "Not Viewed" for letter in all_letters_api)
        ]

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Could not fetch data from the API: {e}")
        # Keep user_contacts, user_letters as empty lists and conditions as False
    except requests.exceptions.JSONDecodeError:
        messages.error(request, "Failed to parse data received from the API.")
         # Keep user_contacts, user_letters as empty lists and conditions as False
    orders = [
            Order.objects.filter(email=user_email),
            Order.objects.filter(status="Completed", email=user_email),
            Order.objects.filter(status="Pending", email=user_email)
        ]

    # Prepare context for the template
    context = {
        'contacts': user_contacts, # Use data filtered from API
        'letters': user_letters,   # Use data filtered from API
        'form': form,              # The Django form for user updates
        'co': conditions,
        "orders": orders
    }

    return render(request, 'profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        user = Usert.objects.get(email=request.user.email)
        if form.is_valid():
            email_changed = form.cleaned_data['email'] != user.email
            user = form.save(commit=False)  # Don't save yet

            if email_changed:
                user.is_verified = False
                messages.warning(request, "Email has been changed. You need to verify your new email address.")
            else:
                messages.success(request, "Changes saved.")

            user.save()  # Now save including is_verified
            return redirect('profile', email=user.email)



    else:   
        form = UserUpdateForm(instance=request.user)
    return redirect('profile', email=request.user.email)

    
    user_email = request.user.email
    contacts = Contact.objects.filter(email=user_email)
    letters = Letter.objects.filter(email=user_email)
    
    return render(request, 'profile.html', {'contacts': contacts, 'letters': letters, 'form': form})



def custom_404_view(request, exception):
    return render(request, '404.html', {
        'exception': exception
    }, status=404)

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        user = request.user

        if not user.check_password(old_password):
            messages.error(request, '❌ Old password is incorrect.')
            return redirect(request.META.get('HTTP_REFERER'))
        if new_password1 != new_password2:
            messages.error(request, '❌ New passwords do not match.')
            return redirect(request.META.get('HTTP_REFERER'))

        if len(new_password1) < 6:
            messages.error(request, '❌ Password must be at least 6 characters.')
            return redirect(request.META.get('HTTP_REFERER'))

        # Change password
        user.set_password(new_password1)
        user.save()
        update_session_auth_hash(request, user) 
        messages.success(request, '✅ Password changed successfully.')
        return redirect('profile',email=request.user.email)  
     
    return redirect('profile',email=request.user.email) 

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            if request.user.is_authenticated:
                email = request.user.email
            else:
                messages.error(request, 'Please enter your email.')
                return redirect(request.META.get('HTTP_REFERER', 'login'))

        try:
            user = Usert.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp

            # send mail
            send_mail(
                subject="Your PetCare Email Verification Code",
                message=f"""
Hi {user.username},

We received a request to change the password for your PetCare account.

Your one-time verification code is: {otp}

Please enter this code on the PetCare website or app to complete your verification. This code will expire in 10 minutes. For your security, do not share this code with anyone.

If you didn’t request this, you can safely ignore this email.

Thanks,  
The PetCare Team  
https://www.petcare.com

PetCare Inc. | 123 Paw Street | New York, NY 10001
""",  # plain text fallback

                from_email='parkspaws.petcare@gmail.com',
                recipient_list=[email],
                html_message=f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <p>Hi {user.username},</p>
    <p>We received a request to change the password for your PetCare account.</p>
    <p>Your one-time verification code is:</p>
    <p style="font-size: 24px; font-weight: bold; color: #2c7be5;">{otp}</p>
    <p>Please enter this code on the PetCare website or app to complete your verification. This code will expire in 10 minutes. For your security, do not share this code with anyone.</p>
    <p>If you didn’t request this, you can safely ignore this email.</p>
    <br>
    <p>Thanks,<br>The PetCare Team</p>
    <p><a href="https://www.petcare.com">https://www.petcare.com</a></p>
    <footer style="font-size: 12px; color: #888;">
      <p>PetCare Inc. | 123 Paw Street | New York, NY 10001</p>
    </footer>
  </body>
</html>
""",
                fail_silently=False,
            )

            messages.success(request, 'OTP sent to your email.')
            request.session['otp_sent'] = True
            return redirect('verify_otp')

        except Usert.DoesNotExist:
            messages.error(request, 'Email not registered.')

    return render(request, 'forgot_password.html')
def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            if request.user.is_authenticated:
                email = request.user.email
            else:
                messages.error(request, 'Please enter your email.')
                return redirect(request.META.get('HTTP_REFERER', 'forgot_password'))

        try:
            user = Usert.objects.get(email=email)
            otp = str(random.randint(100000, 999999))
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp

            # send mail
            send_mail(
                subject="Your PetCare Email Verification Code",
                message=f"""
Hi {user.username},

We received a request to change the password for your PetCare account.

Your one-time verification code is: {otp}

Please enter this code on the PetCare website or app to complete your verification. This code will expire in 10 minutes. For your security, do not share this code with anyone.

If you didn’t request this, you can safely ignore this email.

Thanks,  
The PetCare Team  
https://www.petcare.com

PetCare Inc. | 123 Paw Street | New York, NY 10001
""",  # plain text fallback

                from_email='parkspaws.petcare@gmail.com',
                recipient_list=[email],
                html_message=f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <p>Hi {user.username},</p>
    <p>We received a request to change the password for your PetCare account.</p>
    <p>Your one-time verification code is:</p>
    <p style="font-size: 24px; font-weight: bold; color: #2c7be5;">{otp}</p>
    <p>Please enter this code on the PetCare website or app to complete your verification. This code will expire in 10 minutes. For your security, do not share this code with anyone.</p>
    <p>If you didn’t request this, you can safely ignore this email.</p>
    <br>
    <p>Thanks,<br>The PetCare Team</p>
    <p><a href="https://www.petcare.com">https://www.petcare.com</a></p>
    <footer style="font-size: 12px; color: #888;">
      <p>PetCare Inc. | 123 Paw Street | New York, NY 10001</p>
    </footer>
  </body>
</html>
""",
                fail_silently=False,
            )

            messages.success(request, 'OTP sent to your email.')
            request.session['otp_sent'] = True
            return redirect('verify_otp',email=email)

        except Usert.DoesNotExist:
            messages.error(request, 'Email not registered.')

    return render(request, 'forgot_password.html')

def verify_otp_view(request,email):
    if request.method == 'POST':
        entered_otp = ''.join([request.POST.get(f'digit{i}', '') for i in range(1, 7)])

        session_otp = request.session.get('reset_otp')
        if entered_otp == session_otp:
            request.session['otp_verified'] = True
            messages.success(request, 'OTP verified. Set a new password.')
            return redirect('set_new_password')
        else:
            messages.error(request, 'Incorrect OTP.')
    if request.session.get('otp_sent'):
        return render(request, 'verify_otp.html',{"email":email})
    else:
        raise Http404("You're not allowed to access this page.")
     

def set_new_password_view(request):
    if request.session.get('otp_verified'):
        request.session['otp_sent'] = False

        email = request.session.get('reset_email')
        if request.method == 'POST':
            pass1 = request.POST['new_password1']
            pass2 = request.POST['new_password2']

            if pass1 == pass2:
                try:
                    if request.user.is_authenticated :
                        user = Usert.objects.get(email=email)
                        user.set_password(pass1)
                        user.is_verified = True
                        user.save()
                        send_mail(
                            subject = "Your PetCare Email Verification Code",
                            message =f"""
Hi {user.username },

We’re letting you know that your password was successfully changed.

If you made this change, no further action is needed.

If you did **not** change your password, please reset your password immediately by clicking the link below or contact support:

🔗 Reset Password through our site.

Keeping your account safe is our top priority.

Thanks,  
The PetCare Team  
https://www.petcare.com

PetCare Inc. | 123 Paw Street | New York, NY 10001  
""",

                            from_email='parkspaws.petcare@gmail.com',
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        # 💡 Try updating session (if user is logged in)
                        if request.user.is_authenticated and request.user == user:
                            update_session_auth_hash(request, user)
                        else:
                            # 👇 Re-authenticate and log them in if coming from OTP link or not logged in
                            user = authenticate(request, username=user.username, password=pass1)
                            if user is not None:
                                login(request, user)

                        messages.success(request, 'Password changed successfully.')
                        request.session['otp_verified'] = False
                        #so that user cant change password after change once
                        return redirect('profile' , email=request.user.email)  
                    else:
                        user = Usert.objects.get(email=email)
                        user.set_password(pass1)
                        # user.is_verified = True
                        user.save()

                        messages.success(request, 'Password changed successfully.')
                        request.session['otp_verified'] = False
                        #so that user cant change password after change once
                        return redirect('login')  
                except Usert.DoesNotExist:
                    messages.error(request, 'User not found.')
                except Exception as e:
                    messages.error(request, f'Something went wrong: {str(e)}')
            else:
                messages.error(request, 'Passwords do not match.')


        return render(request, 'set_new_password.html')
    raise Http404("You're not allowed to access this page.")


# === Contact Form ===
# @login_required
# def contact_view(request):
#     if request.method == 'POST':
#         Contact.objects.create(
#             username=request.POST['username'],
#             number=request.POST['phone'],
#             email=request.POST['email'],
#             type=request.POST['type'],
#             location=request.POST['location'],
#             message=request.POST['message'],
#             pname=request.POST['pet-name'],
#             pid=request.POST['pet-id']
#         )
#         messages.success(request, "Contact form submitted")
#     return render(request, 'contact.html')


# def delete_contact(request, id):
#     if request.method=='POST':
#         try:
#             contact = get_object_or_404(Contact, id=id)
#             contact.delete()
#         except 404:
#             messages.error(request,"request not found")
#         return redirect(request.META.get('HTTP_REFERER', 'home')) 
#     else:
#         raise Http404("You're not allowed to access this page.")

# def delete_letter(request, id):
#     if request.method=='POST':
#         try:
#             letter = get_object_or_404(Letter, id=id)
#             letter.delete()
#         except 404:
#             messages.error(request,"letter not found")
#         return redirect(request.META.get('HTTP_REFERER', 'home')) 
#     else:
#         raise Http404("You're not allowed to access this page.")


# # === Letter Form ===
# @login_required
# def letter_view(request):
#     if request.method == 'POST':
#         Letter.objects.create(
#             username=request.POST['username'],
#             email=request.POST['email'],
#             number=request.POST['phone'],
#             location=request.POST['location'],
#             message=request.POST['message']
#         )
#         messages.success(request, "Letter submitted")
#         return redirect('contact')
#     return render(request, 'contact.html')


@login_required
def contact_view(request):
    """
    Handles displaying the contact form (GET) and submitting
    contact data to the Flask API (POST).
    """
    if request.method == 'POST':
        # Prepare data payload for the Flask API
        payload = {
            'username': request.POST.get('username'),
            'number': request.POST.get('phone'), # Map form field 'phone' to API field 'number'
            'email': request.POST.get('email'),
            'type': request.POST.get('type'),
            'location': request.POST.get('location'),
            'message': request.POST.get('message'),
            'pname': request.POST.get('pet-name'), # Map form field 'pet-name' to API field 'pname'
            'pid': request.POST.get('pet-id')      # Map form field 'pet-id' to API field 'pid'
            # 'last_updated_by_id' could be added here if needed: request.user.id
        }

        # Basic frontend validation (optional, but good practice)
        if not all(payload.values()): # Simple check if any value is missing
             messages.error(request, "Please fill in all required fields.")
             return render(request, 'contact.html', {'form_data': payload}) # Pass data back to form

        try:
            # Send POST request to the Flask API's /contacts endpoint
            response = requests.post(f"{FLASK_API_URL}/contacts", json=payload)

            # Check if the API request was successful (e.g., 201 Created)
            if response.status_code == 201:
                messages.success(request, "Contact form submitted successfully!")
                # Redirect to a relevant page, maybe a 'thank you' page or back home
                return redirect('home') # Or wherever appropriate
            else:
                # Try to get a specific error message from the API response
                try:
                    error_detail = response.json().get('message', 'Unknown API error.')
                except requests.exceptions.JSONDecodeError:
                    error_detail = response.text
                messages.error(request, f"Failed to submit contact form. API Error: {error_detail} (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            # Handle network errors (e.g., Flask API not running)
            messages.error(request, f"Could not connect to the contact service: {e}")

        # If POST fails, re-render the form, potentially with submitted data
        return render(request, 'contact.html', {'form_data': payload})

    # For GET requests, just render the empty contact form
    return render(request, 'contact.html')


@login_required # Keep login required for deletion actions
def delete_contact(request, id):
    """
    Handles deleting a contact entry via the Flask API (POST request).
    """
    if request.method == 'POST':
        try:
            # Send DELETE request to the Flask API's /contacts/<id> endpoint
            response = requests.delete(f"{FLASK_API_URL}/contacts/{id}")

            # Check if the API request was successful (e.g., 200 OK or 204 No Content)
            if response.status_code == 200 or response.status_code == 204:
                messages.success(request, "Contact request deleted successfully.")
            elif response.status_code == 404:
                 messages.error(request, "Contact request not found in the API.")
            else:
                # Try to get a specific error message from the API response
                try:
                    error_detail = response.json().get('message', 'Unknown API error.')
                except requests.exceptions.JSONDecodeError:
                    error_detail = response.text
                messages.error(request, f"Failed to delete contact request. API Error: {error_detail} (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            # Handle network errors
            messages.error(request, f"Could not connect to the contact service: {e}")

        # Redirect back to the previous page or a default page
        return redirect(request.META.get('HTTP_REFERER', reverse('home'))) # Use reverse for safety

    else:
        # Disallow GET requests for deletion
        messages.error(request, "Invalid request method for deleting contact.")
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))


@login_required # Keep login required for deletion actions
def delete_letter(request, id):
    """
    Handles deleting a letter entry via the Flask API (POST request).
    """
    if request.method == 'POST':
        try:
            # Send DELETE request to the Flask API's /letters/<id> endpoint
            response = requests.delete(f"{FLASK_API_URL}/letters/{id}")

            # Check if the API request was successful (e.g., 200 OK or 204 No Content)
            if response.status_code == 200 or response.status_code == 204:
                messages.success(request, "Letter deleted successfully.")
            elif response.status_code == 404:
                 messages.error(request, "Letter not found in the API.")
            else:
                # Try to get a specific error message from the API response
                try:
                    error_detail = response.json().get('message', 'Unknown API error.')
                except requests.exceptions.JSONDecodeError:
                    error_detail = response.text
                messages.error(request, f"Failed to delete letter. API Error: {error_detail} (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            # Handle network errors
            messages.error(request, f"Could not connect to the letter service: {e}")

        # Redirect back to the previous page or a default page
        return redirect(request.META.get('HTTP_REFERER', reverse('home'))) # Use reverse for safety

    else:
        # Disallow GET requests for deletion
        messages.error(request, "Invalid request method for deleting letter.")
        return redirect(request.META.get('HTTP_REFERER', reverse('home')))


@login_required
def letter_view(request):
    """
    Handles displaying the letter form (GET) and submitting
    letter data to the Flask API (POST). Assumes it uses the same template 'contact.html'.
    """
    if request.method == 'POST':
        # Prepare data payload for the Flask API
        payload = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'number': request.POST.get('phone'), # Map form field 'phone' to API field 'number'
            'location': request.POST.get('location'),
            'message': request.POST.get('message')
             # 'last_updated_by_id' could be added here if needed: request.user.id
        }

        # Basic frontend validation
        if not all(payload.values()):
             messages.error(request, "Please fill in all required fields.")
             # Assuming the same template is used, pass data back
             return render(request, 'contact.html', {'form_data': payload})

        try:
            # Send POST request to the Flask API's /letters endpoint
            response = requests.post(f"{FLASK_API_URL}/letters", json=payload)

            # Check if the API request was successful (e.g., 201 Created)
            if response.status_code == 201:
                messages.success(request, "Letter submitted successfully!")
                # Redirect to contact page as per original code, or elsewhere if needed
                return redirect('contact')
            else:
                # Try to get a specific error message from the API response
                try:
                    error_detail = response.json().get('message', 'Unknown API error.')
                except requests.exceptions.JSONDecodeError:
                    error_detail = response.text
                messages.error(request, f"Failed to submit letter. API Error: {error_detail} (Status: {response.status_code})")

        except requests.exceptions.RequestException as e:
            # Handle network errors
            messages.error(request, f"Could not connect to the letter service: {e}")

        # If POST fails, re-render the form
        return render(request, 'contact.html', {'form_data': payload})

    # For GET requests, render the form (assuming it's the same contact.html template)
    return render(request, 'contact.html')
# === Blog Creation ===
@login_required
def create_blog(request):
    if request.method == 'POST':
        id = request.POST['id']

        # Check if the ID already exists
        if Blog.objects.filter(id=id).exists():
            messages.error(request, "ID already exists! Please use a unique ID.")
            return redirect('blog')

        photo = request.FILES['photo']
        if not photo:
            messages.error(request, "No photo selected.")
            return redirect(request.META.get('HTTP_REFERER', 'blog'))

        type = request.POST['type']
        pet_name = request.POST['pname']
        heading_explanation = request.POST['heading_explanation']
        subheadings = "**".join(request.POST.getlist('subheading[]'))
        explanations = "**".join(request.POST.getlist('explanation[]'))

        # Custom file path
        upload_folder = os.path.join('home','static', 'images', 'uploads', 'pets')
        os.makedirs(upload_folder, exist_ok=True)

        filename = photo.name
        filepath = os.path.join(upload_folder, filename)

        with open(filepath, 'wb+') as destination:
            for chunk in photo.chunks():
                destination.write(chunk)

        Blog.objects.create(
            id=id,
            photo=photo,  # Save the relative path if you plan to render it
            type=type,
            pet_name=pet_name,
            heading_explanation=heading_explanation,
            subheadings=subheadings,
            explanations=explanations
        )
        messages.success(request, "Blog added successfully!")
        return redirect('blog')

    return render(request, 'create_blog.html')

# @login_required
# def staff_view(request):
#     if request.user.is_staff or request.user.is_superuser:
#         users = Usert.objects.filter(is_staff=False)
#         admins = Usert.objects.filter(Q(is_staff=True) | Q(is_superuser=True))

#         contacts = Contact.objects.all()
#         letters = Letter.objects.all()
#         cards = Blog.objects.all()
#         existing_ids = [card.id for card in cards]
#         conditions = [
#         any(contact.status=="accepted" for contact in Contact.objects.all()),  # Condition 1
#         any(contact.status=="declined" for contact in Contact.objects.all()),  # Condition 2
#         any(contact.status=="pending" for contact in Contact.objects.all()),   # Condition 3
#         any(letter.status=="Viewed" for letter in Letter.objects.all()),       # Condition 4
#         any(letter.status=="Not Viewed" for letter in Letter.objects.all())    # Condition 5
#         ]
#         orders={
#             "total":Order.objects.all(),
#             "completed": Order.objects.filter(status="Completed"),
#             "pending":Order.objects.filter(status="Pending")
#         }
       

#         return render(request, "staff.html", {
#             "admins": admins,
#             "users": users,
#             "contacts": contacts,
#             "letters": letters,
#             "cards": cards,
#             "existing_ids": existing_ids,
#             "co":conditions,
#             "orders": orders,
#         })
#     else:
#         return redirect('lofin')


# @login_required
# def admin_view(request):
#     if request.user.is_superuser:
#         users = Usert.objects.filter(is_staff=False)
#         admins = Usert.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
#         contacts = Contact.objects.all()
#         letters = Letter.objects.all()
#         cards = Blog.objects.all()
#         existing_ids = [card.id for card in cards]
#         conditions = [
#         any(contact.status=="accepted" for contact in Contact.objects.all()),  # Condition 1
#         any(contact.status=="declined" for contact in Contact.objects.all()),  # Condition 2
#         any(contact.status=="pending" for contact in Contact.objects.all()),   # Condition 3
#         any(letter.status=="Viewed" for letter in Letter.objects.all()),       # Condition 4
#         any(letter.status=="Not Viewed" for letter in Letter.objects.all())    # Condition 5
#         ]
    
#         orders=[
#             Order.objects.all(),
#             Order.objects.filter(status="Completed"),
#             Order.objects.filter(status="Pending")
#         ]
   

#         return render(request, "superuser.html", {
#             "admins": admins,
#             "users": users,
#             "contacts": contacts,
#             "letters": letters,
#             "cards": cards,
#             "existing_ids": existing_ids,
#             "co":conditions,
#             "orders": orders,
#         })
#     else:
#         return redirect('login')



@login_required
def staff_view(request):
    """
    Displays a dashboard for staff users, fetching contacts and letters
    from the Flask API and other data from the Django database.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        # Redirect non-staff/superusers away, maybe to home or login
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home') # Or 'login' if appropriate

    # --- Data from Django DB ---
    users = Usert.objects.filter(is_staff=False)
    admins = Usert.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
    cards = Blog.objects.all()
    existing_ids = [card.id for card in cards]
    try:
        orders_data = [
            Order.objects.all(),
            Order.objects.filter(status="Completed"),
            Order.objects.filter(status="Pending")
        ]
    except Exception as e: # Catch potential errors if Order model or fields change
        messages.error(request, f"Could not fetch order data: {e}")
        orders_data = {"total": [], "completed": [], "pending": []} # Default empty

    # --- Data from Flask API ---
    contacts_api = []
    letters_api = []
    conditions = [False] * 5 # Initialize conditions

    try:
        # Fetch ALL contacts from Flask API
        contacts_response = requests.get(f"{FLASK_API_URL}/contacts")
        contacts_response.raise_for_status()
        contacts_api = contacts_response.json()

        # Fetch ALL letters from Flask API
        letters_response = requests.get(f"{FLASK_API_URL}/letters")
        letters_response.raise_for_status()
        letters_api = letters_response.json()

        # Calculate conditions based on ALL contacts and letters from API
        conditions = [
            any(contact.get('status') == "accepted" for contact in contacts_api),
            any(contact.get('status') == "declined" for contact in contacts_api),
            any(contact.get('status') == "pending" for contact in contacts_api),
            any(letter.get('status') == "Viewed" for letter in letters_api),
            any(letter.get('status') == "Not Viewed" for letter in letters_api)
        ]

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Could not fetch contact/letter data from the API: {e}")
    except requests.exceptions.JSONDecodeError:
         messages.error(request, "Failed to parse contact/letter data received from the API.")

    # --- Prepare Context ---
    context = {
        "admins": admins,
        "users": users,
        "contacts": contacts_api, # Use data from API
        "letters": letters_api,   # Use data from API
        "cards": cards,
        "existing_ids": existing_ids,
        "co": conditions,         # Use conditions from API data
        "orders": orders_data,
    }
    return render(request, "staff.html", context)


@login_required
def admin_view(request):
    """
    Displays a dashboard for superusers, fetching contacts and letters
    from the Flask API and other data from the Django database.
    """
    if not request.user.is_superuser:
        # Redirect non-superusers away
        messages.error(request, "You do not have permission to access this page.")
        return redirect('home') # Or 'login'

    # --- Data from Django DB ---
    users = Usert.objects.filter(is_staff=False)
    admins = Usert.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
    cards = Blog.objects.all()
    existing_ids = [card.id for card in cards]
    try:
        # Note: Original code had orders as a list, changed to dict for consistency
        orders_data = [
            Order.objects.all(),
            Order.objects.filter(status="Completed"),
            Order.objects.filter(status="Pending")
        ]

    except Exception as e:
        messages.error(request, f"Could not fetch order data: {e}")
        orders_data = {"total": [], "completed": [], "pending": []}


    # --- Data from Flask API ---
    contacts_api = []
    letters_api = []
    conditions = [False] * 5 # Initialize conditions

    try:
        # Fetch ALL contacts from Flask API
        contacts_response = requests.get(f"{FLASK_API_URL}/contacts")
        contacts_response.raise_for_status()
        contacts_api = contacts_response.json()

        # Fetch ALL letters from Flask API
        letters_response = requests.get(f"{FLASK_API_URL}/letters")
        letters_response.raise_for_status()
        letters_api = letters_response.json()

        # Calculate conditions based on ALL contacts and letters from API
        conditions = [
            any(contact.get('status') == "accepted" for contact in contacts_api),
            any(contact.get('status') == "declined" for contact in contacts_api),
            any(contact.get('status') == "pending" for contact in contacts_api),
            any(letter.get('status') == "Viewed" for letter in letters_api),
            any(letter.get('status') == "Not Viewed" for letter in letters_api)
        ]

    except requests.exceptions.RequestException as e:
        messages.error(request, f"Could not fetch contact/letter data from the API: {e}")
    except requests.exceptions.JSONDecodeError:
         messages.error(request, "Failed to parse contact/letter data received from the API.")

    # --- Prepare Context ---
    context = {
        "admins": admins,
        "users": users,
        "contacts": contacts_api, # Use data from API
        "letters": letters_api,   # Use data from API
        "cards": cards,
        "existing_ids": existing_ids,
        "co": conditions,         # Use conditions from API data
        "orders": orders_data,    # Use dict structure
    }

    return render(request, "superuser.html", context) # Assuming template is superuser.html

@login_required
def delete_user(request, username):
    referer_url = request.META.get('HTTP_REFERER', None)
    if request.method == 'POST':
        user_to_delete = get_object_or_404(Usert, username=username)
        
        if request.user != user_to_delete:  # Optional: prevent deleting yourself
            user_to_delete.delete()
            messages.success(request, f"User '{username}' has been deleted successfully.")  # Success message
        else:
            messages.warning(request, "You cannot delete your own account.")  # Warning message if user tries to delete themselves
        if referer_url:
            return redirect(referer_url)  # Redirect to the referer (previous page)
        else:
            return redirect('staff')
    
    messages.error(request, "Invalid request method.")  # Error message if not POST
    return redirect('home') # Fallback to 'staff' if no referer is found



# ✅ Update status for Contacts
# @login_required
# @require_POST
# def update_status(request):
#     con_ids = request.POST.getlist('con_ids')
#     status = request.POST.get('status')

#     if con_ids:
#         if status == "del":
#             for contact_id in con_ids:
#                 entry = Contact.objects.filter(id=contact_id).first()
#                 if entry:
#                     entry.delete()
#         else:
#             for contact_id in con_ids:
#                 cont = Contact.objects.filter(id=contact_id).first()
#                 Contact.objects.filter(id=contact_id).update(status=status)
#                 print(cont.username)
#                 if status=="accepted":
#                     send_mail(
#                             subject = "🎉 Your PetCare Request Has Been Accepted!",
#                             message = f"""
# Hi {cont.username},

# Great news! Your recent request has been **accepted** ✅

# We are pleased to inform you that your recent request for {cont.type} regarding your pet, {cont.pname}, has been successfully accepted. Your dedication and patience throughout this process are greatly appreciated.

# Our records show that this request was submitted by {cont.username} ({cont.email}), and the current status of your request has been updated to **{cont.status}**. We are excited to continue supporting you and your pet as we move forward.

# If you have any questions or need additional assistance, please do not hesitate to contact us.

# Warm regards,  
# {cont.last_updated_by}  
# The PetCare Team  
# https://www.petcare.com
# """,
                    

#                             from_email='parkspaws.petcare@gmail.com',
#                             recipient_list=[cont.email],
#                             fail_silently=False,
#                         )
#                 else:
#                     send_mail(
#                             subject = "⚠️ Update on Your PetCare Request",
#                             message = f"""
# Hi {cont.username},

# We wanted to let you know that your recent request has been **declined** ❌

# We regret to inform you that your recent request for {cont.type} regarding your pet, {cont.pname}, has not been approved and is now marked as **declined**. The request was submitted by {cont.username} ({cont.email}), and we have reviewed the details thoroughly.

# While we understand this may be disappointing, we encourage you to reach out to us for more information or clarification regarding the reasons behind this decision. You may also consider reapplying with the necessary adjustments.

# Thank you for your understanding, and we appreciate your continued interest in PetCare.

# Sincerely,  
# {cont.last_updated_by}  
# The PetCare Team  
# https://www.petcare.com
# """,
                    

#                             from_email='parkspaws.petcare@gmail.com',
#                             recipient_list=[cont.email],
#                             fail_silently=False,
#                         )

#     return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))


@login_required
@require_POST # Ensures this view only accepts POST requests
def update_status(request):
    """
    Updates the status or deletes Contact entries via the Flask API
    based on the submitted form data. Sends notification emails on status change.
    """
    con_ids = request.POST.getlist('con_ids') # Get list of contact IDs
    status_action = request.POST.get('status') # Get the desired action ('accepted', 'declined', 'del')

    if not con_ids:
        messages.warning(request, "No contacts selected.")
        return redirect(request.META.get('HTTP_REFERER', 'home')) # Redirect back

    if not status_action:
        messages.error(request, "No action specified.")
        return redirect(request.META.get('HTTP_REFERER', 'home')) # Redirect back

    success_count = 0
    error_count = 0
    error_messages = []

    # Determine the email sender name (use full name if available, otherwise username)
    sender_name = request.user.get_full_name() or request.user.username
    # Get the default from email from settings, or use a hardcoded one
    # from_email_address = getattr(settings, 'DEFAULT_FROM_EMAIL', 'parkspaws.petcare@gmail.com')


    for contact_id in con_ids:
        try:
            contact_id_int = int(contact_id) # Ensure ID is an integer
            api_url = f"{FLASK_API_URL}/contacts/{contact_id_int}"

            if status_action == "del":
                # --- Handle Deletion ---
                response = requests.delete(api_url)
                if response.status_code in [200, 204]: # OK or No Content
                    success_count += 1
                elif response.status_code == 404:
                    error_messages.append(f"Contact ID {contact_id_int} not found in API.")
                    error_count += 1
                else:
                    error_messages.append(f"Failed to delete Contact ID {contact_id_int}. API Status: {response.status_code}")
                    error_count += 1

            elif status_action in ["accepted", "declined"]:
                # --- Handle Status Update ---
                payload = {
                    'status': status_action,
                    'last_updated_by': request.user.username # Send the Django user ID
                }
                response = requests.put(api_url, json=payload)

                if response.status_code == 200: # OK
                    success_count += 1
                    try:
                        # Get contact details from the API response for the email
                        updated_contact_data = response.json().get("contact", {})
                        cont_username = updated_contact_data.get("username", "there")
                        cont_email = updated_contact_data.get("email")
                        cont_type = updated_contact_data.get("type", "your request")
                        cont_pname = updated_contact_data.get("pname", "your pet")
                        cont_status = updated_contact_data.get("status", status_action) # Use updated status

                        if not cont_email:
                             error_messages.append(f"Could not send email for Contact ID {contact_id_int}: Email missing in API response.")
                             continue # Skip email sending for this one

                        # --- Send Email ---
                        if status_action == "accepted":
                            subject = "🎉 Your PetCare Request Has Been Accepted!"
                            message_body = f"""
Hi {cont_username},

Great news! Your recent request has been **accepted** ✅

We are pleased to inform you that your recent request for {cont_type} regarding {cont_pname} has been successfully accepted. Your dedication and patience throughout this process are greatly appreciated.

Our records show that this request was submitted by {cont_username} ({cont_email}), and the current status of your request has been updated to **{cont_status}**. We are excited to continue supporting you and your pet as we move forward.

If you have any questions or need additional assistance, please do not hesitate to contact us.

Warm regards,
{sender_name}
The PetCare Team
https://www.petcare.com
"""
                        else: # Declined
                            subject = "⚠️ Update on Your PetCare Request"
                            message_body = f"""
Hi {cont_username},

We wanted to let you know that your recent request has been **declined** ❌

We regret to inform you that your recent request for {cont_type} regarding {cont_pname} has not been approved and is now marked as **{cont_status}**. The request was submitted by {cont_username} ({cont_email}), and we have reviewed the details thoroughly.

While we understand this may be disappointing, we encourage you to reach out to us for more information or clarification regarding the reasons behind this decision. You may also consider reapplying with the necessary adjustments.

Thank you for your understanding, and we appreciate your continued interest in PetCare.

Sincerely,
{sender_name}
The PetCare Team
https://www.petcare.com
"""
                        # Send the actual email
                        send_mail(
                            subject=subject,
                            message=message_body, # Use plain text version
                            from_email='parkspaws.petcare@gmail.com',
                            recipient_list=[cont_email],
                            fail_silently=False, # Raise error if email fails
                            # Consider adding html_message=... for formatted emails
                        )

                    except requests.exceptions.JSONDecodeError:
                        error_messages.append(f"Contact ID {contact_id_int} updated, but failed to parse API response for email.")
                    except Exception as mail_error:
                        error_messages.append(f"Contact ID {contact_id_int} updated, but failed to send email: {mail_error}")
                        # Still counts as a successful update, but log email error

                elif response.status_code == 404:
                    error_messages.append(f"Contact ID {contact_id_int} not found in API.")
                    error_count += 1
                elif response.status_code == 400:
                     error_messages.append(f"Failed to update Contact ID {contact_id_int}. Invalid data sent to API (e.g., bad status).")
                     error_count += 1
                else:
                    error_messages.append(f"Failed to update Contact ID {contact_id_int}. API Status: {response.status_code}")
                    error_count += 1
            else:
                # Invalid status action provided
                error_messages.append(f"Invalid action '{status_action}' for Contact ID {contact_id_int}.")
                error_count += 1

        except ValueError:
            error_messages.append(f"Invalid Contact ID format: {contact_id}.")
            error_count += 1
        except requests.exceptions.RequestException as e:
            error_messages.append(f"Network error processing Contact ID {contact_id}: {e}")
            error_count += 1
        except Exception as e: # Catch any other unexpected errors
             error_messages.append(f"An unexpected error occurred processing Contact ID {contact_id}: {e}")
             error_count += 1


    # --- Report Results ---
    if success_count > 0:
        action_verb = "deleted" if status_action == "del" else "updated"
        messages.success(request, f"Successfully {action_verb} {success_count} contact(s).")

    if error_count > 0:
        # Combine specific errors into one message or show separately
        full_error_message = f"Failed to process {error_count} contact(s). Errors: " + "; ".join(error_messages)
        messages.error(request, full_error_message)

    # Redirect back to the previous page
    return redirect(request.META.get('HTTP_REFERER', 'home')) # Use 'home' as fallback


# ✅ Update status for Letters
# @login_required
# @require_POST
# def update_status_letter(request):
#     lett_ids = request.POST.getlist('lett_ids')
#     status = request.POST.get('status')

#     if lett_ids:
#         if status == "del":
#             for letter_id in lett_ids:
#                 entry = Letter.objects.filter(id=letter_id).first()
#                 if entry:
#                     entry.delete()
#         else:
#             Letter.objects.filter(id__in=lett_ids).update(status=status)

#     return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))


@login_required
@require_POST # Ensures this view only accepts POST requests
def update_status_letter(request):
    """
    Updates the status or deletes Letter entries via the Flask API
    based on the submitted form data.
    """
    lett_ids = request.POST.getlist('lett_ids') # Get list of letter IDs
    status_action = request.POST.get('status') # Get the desired action ('Viewed', 'Not Viewed', 'del')

    # --- Input Validation ---
    if not lett_ids:
        messages.warning(request, "No letters selected.")
        return redirect(request.META.get('HTTP_REFERER', 'home')) # Redirect back

    if not status_action:
        messages.error(request, "No action specified.")
        return redirect(request.META.get('HTTP_REFERER', 'home')) # Redirect back

    # Define valid status updates for letters (excluding 'del')
    valid_statuses = ["Viewed", "Not Viewed"]

    success_count = 0
    error_count = 0
    error_messages = []

    for letter_id in lett_ids:
        try:
            letter_id_int = int(letter_id) # Ensure ID is an integer
            api_url = f"{FLASK_API_URL}/letters/{letter_id_int}"

            if status_action == "del":
                # --- Handle Deletion ---
                response = requests.delete(api_url)
                if response.status_code in [200, 204]: # OK or No Content
                    success_count += 1
                elif response.status_code == 404:
                    error_messages.append(f"Letter ID {letter_id_int} not found in API.")
                    error_count += 1
                else:
                    error_messages.append(f"Failed to delete Letter ID {letter_id_int}. API Status: {response.status_code}")
                    error_count += 1

            elif status_action in valid_statuses:
                # --- Handle Status Update ---
                payload = {
                    'status': status_action,
                    'last_updated_by': request.user.username # Send the Django user ID
                }
                response = requests.put(api_url, json=payload)

                if response.status_code == 200: # OK
                    success_count += 1
                    # No email sending needed based on original function
                elif response.status_code == 404:
                    error_messages.append(f"Letter ID {letter_id_int} not found in API.")
                    error_count += 1
                elif response.status_code == 400:
                     error_messages.append(f"Failed to update Letter ID {letter_id_int}. Invalid data sent to API (e.g., bad status: '{status_action}').")
                     error_count += 1
                else:
                    error_messages.append(f"Failed to update Letter ID {letter_id_int}. API Status: {response.status_code}")
                    error_count += 1
            else:
                # Invalid status action provided
                error_messages.append(f"Invalid action '{status_action}' for Letter ID {letter_id_int}. Must be 'Viewed', 'Not Viewed', or 'del'.")
                error_count += 1

        except ValueError:
            error_messages.append(f"Invalid Letter ID format: {letter_id}.")
            error_count += 1
        except requests.exceptions.RequestException as e:
            error_messages.append(f"Network error processing Letter ID {letter_id}: {e}")
            error_count += 1
        except Exception as e: # Catch any other unexpected errors
             error_messages.append(f"An unexpected error occurred processing Letter ID {letter_id}: {e}")
             error_count += 1


    # --- Report Results ---
    if success_count > 0:
        action_verb = "deleted" if status_action == "del" else "updated"
        messages.success(request, f"Successfully {action_verb} {success_count} letter(s).")

    if error_count > 0:
        # Combine specific errors into one message or show separately
        full_error_message = f"Failed to process {error_count} letter(s). Errors: " + "; ".join(error_messages)
        messages.error(request, full_error_message)

    # Redirect back to the previous page
    # Note: Original code used 'fallback_url', using 'home' as a safer default
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def blog_delete(request):
    if request.method == 'POST':
        blog_id = request.POST.get("blog_id")

        if not blog_id:
            messages.error(request, "Blog ID is required!")
            return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

        blog = Blog.objects.filter(id=blog_id).first()
        if blog:
            blog.delete()
            messages.success(request, "Blog deleted successfully!")
        else:
            messages.error(request, "Blog ID not found!")

        return redirect(request.META.get('HTTP_REFERER', 'fallback_url'))

    # If it's not a POST request
    messages.error(request, "Invalid request method.")
    return redirect('blog')


def get_pet_data(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        value = data.get('value')
        field = data.get('field')

        if field == 'id':
            pet = Blog.objects.filter(id=value).first()
            if pet:
                return JsonResponse({'pet_name': pet.pet_name})
        elif field == 'name':
            pet = Blog.objects.filter(pet_name=value).first()
            if pet:
                return JsonResponse({'pet_id': pet.id})

    return JsonResponse({})

def doggydaycamp(request):
    return render(request ,'doggydaycamp.html')

def see_pricing(request):
    return render(request ,'boarding.html')

def grooming(request):
    return render(request ,'grooming.html')

def doggycamp(request):
    return render(request , 'doggycamp.html')

def puppyplay(request):
    return render(request ,'PuppyPlayGroup.html')

def faq(request):
    return render(request , 'faq.html')


from django.shortcuts import render, redirect
from django.contrib import messages
from store.models import Order

def order_dashboard(request):
    tab = request.GET.get('tab', 'all')
    1
    if tab == 'completed':
        orders = Order.objects.filter(status="Completed")
    elif tab == 'pending':
        orders = Order.objects.filter(status="Pending")
    else:
        orders = Order.objects.all()

    count = {
        "total": Order.objects.count(),
        "completed": Order.objects.filter(status="Completed").count(),
        "pending": Order.objects.filter(status="Pending").count(),
    }

    return render(request, 'staff', {
        "orders": orders,
        "count": count,
        "active_tab": tab
    })

def update_status_order(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ord_ids')
        status = request.POST.get('status')
        referer_url = request.META.get('HTTP_REFERER', None)
        if status == 'Completed':
            Order.objects.filter(id__in=ids).update(status='Completed')
            messages.success(request, "Selected orders marked as Completed.")
        elif status == 'del':
            Order.objects.filter(id__in=ids).delete()
            messages.success(request, "Selected orders deleted.")
        if referer_url:
            return redirect(referer_url)  # Redirect to the referer (previous page)
        else:
            return redirect('staff')



# # === Contact Admin Views ===
# @login_required
# @user_passes_test(is_admin)
# def view_contacts(request):
#     contacts = Contact.objects.all()
#     return render(request, 'view_contacts.html', {'contacts': contacts})

# @login_required
# @user_passes_test(is_admin)
# def approve_contact(request, id):
#     contact = get_object_or_404(Contact, id=id)
#     contact.status = "V"
#     contact.save()
#     return redirect('view_contacts')

# @login_required
# @user_passes_test(is_admin)
# def reject_contact(request, id):
#     contact = get_object_or_404(Contact, id=id)
#     contact.status = "R"
#     contact.save()
#     return redirect('view_contacts')

# # === Letter Admin Views ===
# @login_required
# @user_passes_test(is_admin)
# def view_letters(request):
#     letters = Letter.objects.all()
#     return render(request, 'view_letters.html', {'letters': letters})

# @login_required
# @user_passes_test(is_admin)
# def approve_letter(request, id):
#     letter = get_object_or_404(Letter, id=id)
#     letter.status = "R"
#     letter.save()
#     return redirect('view_letters')

# @login_required
# @user_passes_test(is_admin)
# def reject_letter(request, id):
#     letter = get_object_or_404(Letter, id=id)
#     letter.status = "NR"
#     letter.save()
#     return redirect('view_letters')

# # === Superadmin View ===
# @login_required
# @user_passes_test(is_superadmin)
# def admin_list(request):
#     admins = Usert.objects.filter(role="admin")
#     return render(request, 'admin_list.html', {'admins': admins})

