Mescon (Message Connector)
Mescon: Your complete real-time communication platform. Chat, Call, Connect.

Mescon is a full-stack, real-time communication application designed to bring you closer to the people who matter. Built with a powerful Python backend using FastAPI and a dynamic vanilla JavaScript frontend, Mescon provides a seamless and secure experience for one-on-one text chats, voice calls, and video calls. The entire system is deployed and live on Render.

✨ Key Features
🔐 Secure OTP Authentication: Get started in seconds. Your mobile number is your identity, secured with a randomly generated one-time password for login.

💾 Persistent & Secure Database: All user data, contacts, and chat history are stored in a robust PostgreSQL database, moving beyond simple file storage.

🤫 Encrypted Chat History: User privacy is paramount. All chat messages are encrypted at rest in the database using the cryptography library, ensuring conversations remain private.

👥 Personal Contact Management (Full CRUD): Each user has their own private address book. You have full control to Add, Edit, and Delete contacts, giving each number a custom name.

👤 Customizable Profiles: Make it your own! Users can set their display name and profile picture (DP) through a dedicated profile management screen.

💬 Real-Time Text Chat: Enjoy instant one-on-one messaging with an intuitive, WhatsApp-like interface. Features include:

Unread Message Badges: A green counter shows you how many new messages you have from each contact.

Detailed Timestamps: Relative timestamps ("Today, 8:55 AM", "Yesterday", etc.) provide a familiar user experience.

📞 High-Quality Voice & Video Calls: Connect with crystal-clear audio or high-definition video powered by WebRTC. The call experience is designed for multitasking:

Accept/Decline Screen: A professional incoming call screen allows users to accept or reject calls.

Movable & Resizable Window: Calls appear in a draggable window that can be minimized or maximized, allowing you to continue texting while you talk.

🌐 Auto-Reconnect: The application is resilient. If the connection to the server is lost, the frontend will automatically try to reconnect every 5 seconds.

📱 Responsive Design: The UI is fully responsive and provides a seamless experience on both desktop and mobile browsers.

🛠️ Tech Stack
This project uses a modern, scalable tech stack, demonstrating a full software development lifecycle from local development to cloud deployment.

Layer

Technology

Purpose

Backend

Python, FastAPI, Uvicorn

For the high-performance, asynchronous server and API endpoints.

Database

PostgreSQL

The robust, relational database for all persistent data.

Real-time

WebSockets & WebRTC

To power instant text chat and peer-to-peer voice/video calls.

Frontend

HTML5, Tailwind CSS, Vanilla JavaScript

For the dynamic, responsive, and modern user interface.

Authentication

JWT (JSON Web Tokens)

To securely manage user sessions after the initial OTP login.

Security

cryptography library

For end-to-end encryption of chat messages stored in the database.

Deployment

Git, GitHub, Render

For version control and deploying the application to a live URL.

🚀 Getting Started
To run this project on your local machine, follow these steps.

Prerequisites
Python 3.9+ and Pip installed.

Git installed on your system.

A free PostgreSQL database (e.g., from Neon).

Installation & Setup
Clone the repository:

git clone [https://github.com/Vjnishad/mescon.git](https://github.com/Vjnishad/mescon.git)
cd mescon

Create and activate a virtual environment:

On Windows:

python -m venv venv
.\venv\Scripts\activate

On macOS/Linux:

python3 -m venv venv
source venv/bin/activate

Install the required packages:

pip install -r requirements.txt

Set up your Environment Variables:

Create a new file in the root of the project named .env.

Generate a secret encryption key by running python to open an interpreter, then:

from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())

Add your database URL and the generated key to your .env file:

DATABASE_URL=YOUR_POSTGRESQL_CONNECTION_STRING
ENCRYPTION_KEY=YOUR_GENERATED_ENCRYPTION_KEY

Run the server:

python main.py

The server will start on http://localhost:8000 and automatically create the necessary database tables on the first run.

Open the application:

Navigate to the static/ folder and open the index.html file in your web browser. The intelligent frontend code will automatically connect to your local server.

🚀 Deployment
This application is deployed and live on Render. The deployment process is configured to:

Read the runtime.txt file to set the Python version.

Install all dependencies from the requirements.txt file.

Run the application using the uvicorn start command.

Securely connect to the production database using Environment Variables configured on the Render dashboard.