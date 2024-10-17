from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from .models import CustomUser
from django.contrib.auth.decorators import login_required
from .models import Conversation
from django.conf import settings 
from django.contrib.auth.forms import AuthenticationForm
from .models import ChatHistory 
import json
import random
import nltk
import os
import string
import warnings
from django.conf import settings
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .models import ChatHistory
from django.db.models import Count
from django.db.models.functions import TruncDate

# Suppress warnings
warnings.filterwarnings('ignore')

# Set custom NLTK data path
nltk_data_path = "C:\\Users\\USER\\AppData\\Roaming\\nltk_data\\tokenizers\\punkt_tab\\"
os.makedirs(nltk_data_path, exist_ok=True)
nltk.data.path.append(nltk_data_path)

# Ensure NLTK resources are available
def ensure_nltk_resources():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', download_dir=nltk_data_path)

    try:
        nltk.data.find('corpora/wordnet')
    except LookupError:
        nltk.download('wordnet', download_dir=nltk_data_path)

# Ensure resources are available at the start
ensure_nltk_resources()

lemmer = WordNetLemmatizer()
 
GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up", "hey",)
GREETING_RESPONSES = ["hi", "hey", "*nods*", "hi there", "hello", "I am glad! You are talking to me"]

def LemTokens(tokens):
    return [lemmer.lemmatize(token) for token in tokens]

def LemNormalize(text):
    remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)
    return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))

def greeting(sentence):
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)
    return None

def response(user_response, sent_tokens):
    robo_response = ''
    sent_tokens.append(user_response)
    
    if len(sent_tokens) > 1:
        TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
        tfidf = TfidfVec.fit_transform(sent_tokens)
        vals = cosine_similarity(tfidf[-1], tfidf)
        
        if vals.shape[1] > 1:
            idx = vals.argsort()[0][-2]
            flat = vals.flatten()
            flat.sort()
            req_tfidf = flat[-2]
            
            if req_tfidf == 0:
                robo_response = "I am sorry! I don't understand you"
            else:
                robo_response = sent_tokens[idx]
        else:
            robo_response = "I need more information to respond effectively."
    else:
        robo_response = "I need more information to respond effectively."

    sent_tokens.pop()
    return robo_response

# Load default texts from file
def load_default_texts():
    text_files_dir = os.path.join(settings.BASE_DIR, 'chat_bot', 'text_files')
    texts = []

    print(f"Loading texts from: {text_files_dir}")  # Debugging line

    try:
        for filename in os.listdir(text_files_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(text_files_dir, filename)
                print(f"Reading file: {file_path}")  # Log the file being read
                with open(file_path, 'r', encoding='utf-8') as file:
                    texts.append(file.read())
    except Exception as e:
        print(f"Error reading text files: {e}")  # Log any exceptions

    return "\n".join(texts)  # Return combined text content

# Load default text content at startup
default_text_content = load_default_texts()
sent_tokens = nltk.sent_tokenize(default_text_content)  # Tokenize the default text

# Chatbot view
def chat_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get("message", "")

        # Generate bot response based on default text file
        response_message = chatbot_response(user_message)

        # Store messages in the database
        Conversation.objects.create(user=request.user, message=user_message)
        Conversation.objects.create(user=request.user, message=response_message)

        return JsonResponse({"response": response_message})

    return render(request, 'chat_bot/chat_interface.html')  # Render chat page for GET requests

# Chatbot response logic
def chatbot_response(user_input):
    if user_input.lower() == 'bye':
        return "Bye! take care.."
    elif greeting(user_input) is not None:
        return greeting(user_input)
    else:
        return response(user_input, sent_tokens)

# Signup view
def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        if len(username) < 3:
            return JsonResponse({"message": "Username must be at least 3 characters long"}, status=400)

        if len(password) < 8:
            return JsonResponse({"message": "Password must be at least 8 characters long"}, status=400)

        if User.objects.filter(username=username).exists():
            return JsonResponse({"message": "Username already exists"}, status=400)

        user = User.objects.create(username=username, password=make_password(password))
        user.save()
        return JsonResponse({"message": "User created successfully"}, status=201)

    return render(request, 'signup.html')

# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')  # Adjust the redirect URL as needed
    else:
        form = AuthenticationForm()
    return render(request, 'chat_bot/login.html', {'form': form})

# Dashboard view
@login_required  # Ensures only logged-in users can access the dashboard
def dashboard(request):
    return render(request, 'chat_bot/dashboard.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def profile_view(request):
    user = request.user  
    signup_date = user.date_joined  
    return render(request, 'profile.html', {'user': user, 'signup_date': signup_date})

@login_required
def chat_history_view(request):
    chat_messages = ChatHistory.objects.all()
    template_path = os.path.join(settings.BASE_DIR, 'templates', 'chat_history.html')
    return render(request, template_path, {'chat_messages': chat_messages})

