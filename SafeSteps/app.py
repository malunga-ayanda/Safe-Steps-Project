from flask import *
from flask_login import *
import qrcode
import os
from werkzeug.security import *
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, date
import uuid
from flask_mailman import Mail, EmailMessage 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'safestepsprjt'

# Email Configs 
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = '465'
app.config['MAIL_USERNAME'] = 'david777bukasa@gmail.com'
app.config['MAIL_PASSWORD'] = 'dixmpocushhvhixj'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

# Initialize the extension
mail.init_app(app)

# Initialize Firebase Admin SDK
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load a user by their ID."""
    user_ref = db.collection('users').where('email', '==', user_id).get()
    if user_ref:
        user_data = user_ref[0].to_dict()
        return User(email=user_data['email'], password=user_data['password'], role=user_data['role'])
    return None

# Path for saving QR codes
qr_codes_path = os.path.join(app.root_path, 'static', 'qr_codes')
if not os.path.exists(qr_codes_path):
    os.makedirs(qr_codes_path)

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, email, password, role):
        self.email = email
        self.password = password
        self.role = role

    @staticmethod
    def get(email):
        """Fetches a user by email from Firestore."""
        user_ref = db.collection('users').where('email', '==', email).get()
        if user_ref:
            user_data = user_ref[0].to_dict()
            return User(email=user_data['email'], password=user_data['password'], role=user_data['role'])
        return None

    def check_password(self, password):
        """Checks if the given password matches the stored hash."""
        return check_password_hash(self.password, password)

    def get_id(self):
        """Returns the email as the user ID (required by Flask-Login)."""
        return self.email


#------------------------------------------------------------------ ROUTES ---------------------------------------------------------------


# Route to Home
@app.route('/')
def index():
    return render_template('index.html')


#------------------------------------------------------------------- AUTH ----------------------------------------------------------------


# Login Code
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Fetch user from Firestore
        user_docs = db.collection('users').where('email', '==', email).get()
        
        if user_docs:  # If the user is found
            user_data = user_docs[0].to_dict()
            user = User(email=user_data['email'], password=user_data['password'], role=user_data['role'])
            
            # Check if the password is correct
            if user and user.check_password(password):
                login_user(user)
                session['parent_id'] = user.get_id()  # Set session for parent ID
                
                # Redirect based on user role
                if user.role == 'Admin':
                    flash('Welcome Admin.', 'success')
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'Parent':
                    flash('Welcome Parent!', 'success')
                    return redirect(url_for('parent_dashboard'))
            else:
                flash('Invalid password. Please try again.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Invalid email. Please try again.', 'danger')
            return redirect(url_for('login'))
    
    return render_template('login.html')



# Logout route
@app.route('/logout', methods=['Post'])
@login_required  # Ensure the user is logged in before allowing logout
def logout():
    # Clear the session
    logout_user()  # This function comes from flask_login
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))  # Redirect to the login page


#--------------------------------------------------------------- USERS DASHBOARDS ------------------------------------------------------------


@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    # Ensure the user is a parent
    if current_user.role != 'Admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))
    
    # Get today's date
    today = date.today().strftime('%Y-%m-%d')

    # Get total number of children, present kids, and absent kids
    total_kids = get_total_kids()
    present_kids = get_present_kids(today)
    absent_kids = total_kids - present_kids

    return render_template('admin_dashboard.html', total_kids=total_kids, present_kids=present_kids, absent_kids=absent_kids)

def get_total_kids():
    # Query Firestore to get total number of kids
    children_ref = db.collection('children')
    children_docs = children_ref.stream()
    return sum(1 for _ in children_docs)

def get_present_kids(today):
    # Query Firestore to get the number of kids who entered today
    entrance_ref = db.collection('entrances').where('date', '==', today)
    entrance_docs = entrance_ref.stream()
    return len(list(entrance_docs))


# Parent Dashboard
@app.route('/parent_dashboard')
@login_required
def parent_dashboard():
    # Ensure the user is a parent
    if current_user.role != 'Parent':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))
    return render_template('parent_dashboard.html')


# ----------------------------------------------------------------- REGISTER USERS ----------------------------------------------------------

# Register Parent (Only Admin can register a parent)
@app.route('/register_parent', methods=['GET', 'POST'])
@login_required
def register_parent():
    if current_user.role != 'Admin':
        flash('You are not authorized to register parents.', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address')
        phone = request.form.get('phone')
        gender = request.form.get('gender')

        # Check if the user already exists
        user_ref = db.collection('users').document(email).get()
        if user_ref.exists:
            flash('Email already exists!', 'danger')
            return redirect(url_for('register_parent'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password)

        # Add the new parent to Firestore
        db.collection('users').document(email).set({
            'email': email,
            'name': name,
            'surname': surname,
            'password': hashed_password,
            'address': address,
            'phone': phone,
            'gender': gender,
            'role': "Parent",
            'registered_at': datetime.utcnow()
        })

        msg=EmailMessage(
            "QR Code for gate entrance at school campus",
            "Dear {surname},\n\nWelcome to Safe Steps.\nBelow is your Login Credentials: Username - {email} Password - {password}",
            "david777bukasa@gmail.com",
            [email]
        )

        flash('Parent registered successfully!', 'success')
        return redirect(url_for('manage_parent'))

    return render_template('register_parent.html')


# Register Child
@app.route('/register-child', methods=['GET', 'POST'])
@login_required
def register_child():
    if current_user.role != 'Admin':
        flash('You are not authorized to register children.', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        grade = request.form.get('grade')
        parent_id = request.form.get('parent_id')
        child_id = request.form.get('id_number')

        # Check if child with this ID already exists
        child_ref = db.collection('children').document(child_id).get()
        if child_ref.exists:
            flash('Child with this ID already exists!', 'danger')
            return redirect(url_for('register_child'))

        # Create QR Code
        qr_img = qrcode.make(f"{name}-{child_id}-{parent_id}")
        qr_code_filename = f'{name}-{child_id}.png'
        qr_code_path = os.path.join(qr_codes_path, qr_code_filename)
        qr_img.save(qr_code_path)

        # Add the new child record to Firestore
        db.collection('children').document(child_id).set({
            'name': name,
            'surname': surname,
            'grade': grade,
            'child_id': child_id,
            'parent_id': parent_id,
            'qr_code_url': f'/static/qr_codes/{qr_code_filename}'
        })

        msg=EmailMessage(
            "QR Code for gate entrance at school campus",
            f"Dear {surname},\n\nAttached is your QR code for your school. Use this to enter/leave the campus at the gate.\n\nBest regards,\nSchool Admin",
            "david777bukasa@gmail.com",
            [parent_id]
        )

        #Open and attach the QR code image in binary mode
        with open(qr_code_path, 'rb') as f:
            qr_code_data = f.read()
            msg.attach(qr_code_path, qr_code_data, 'image/png')

        msg.send()

        flash('Child registered successfully!', 'success')
        return redirect(url_for('manage_learner'))

    # Fetch parents sorted by registration date, descending
    parents_query = db.collection('users').where('role', '==', 'Parent').order_by('registered_at', direction=firestore.Query.DESCENDING).stream()
    parents = [{'id': parent.id, 'name': parent.to_dict().get('name'), 'surname': parent.to_dict().get('surname')} for parent in parents_query]

    return render_template('register_child.html', parents=parents)


# Register a Security
@app.route('/register_security', methods=['GET', 'POST'])
@login_required
def register_security():
    if current_user.role != 'Admin':
        flash('You are not authorized to register security personnel.', 'danger')
        return redirect(url_for('logout'))

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        role = request.form.get('role')
        contact = request.form.get('contact')  # Assuming contact is used as the email

        # Check if the email/contact already exists in the 'securities' collection
        user_ref = db.collection('securities').where('contact', '==', contact).get()
        if user_ref:
            flash('Email/Contact already exists!', 'danger')
            return redirect(url_for('register_security'))

        # Add the new security personnel to Firestore
        db.collection('securities').document(name).set({
            "name": name,
            "password": password,
            "role": role,
            "contact": contact
        })

        flash('Security personnel registered successfully!', 'success')
        return redirect(url_for('manage_security'))

    return render_template('register_security.html')


# ---------------------------------------------------------------- EDIT AND DELETE ----------------------------------------------------------

# Update Parent info
@app.route('/edit-parent/<parent_id>', methods=['GET', 'POST'])
@login_required
def edit_parent(parent_id):
    # Ensure only Admin can edit
    if current_user.role != 'Admin':
        flash('You are not authorized to edit parents.', 'danger')
        return redirect(url_for('logout'))

    parent_ref = db.collection('users').document(parent_id)
    parent = parent_ref.get().to_dict()

    if not parent:
        flash('Parent not found.', 'danger')
        return redirect(url_for('manage_parent'))

    if request.method == 'POST':
        # Update parent data
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        address = request.form.get('address')
        phone = request.form.get('phone')
        gender = request.form.get('gender')
        password = request.form.get('password')

        # Hash the password only if provided
        hashed_password = generate_password_hash(password) if password else parent.get('password')

        parent_ref.update({
            'name': name,
            'surname': surname,
            'email': email,
            'address': address,
            'phone': phone,
            'gender': gender,
            'password': hashed_password,
        })

        flash('Parent updated successfully!', 'success')
        return redirect(url_for('manage_parent'))

    return render_template('edit_parent.html', parent=parent, parent_id=parent_id)


# Update Learner info
@app.route('/edit-learner/<learner_id>', methods=['GET', 'POST'])
@login_required
def edit_learner(learner_id):
    # Ensure only Admin can edit
    if current_user.role != 'Admin':
        flash('You are not authorized to edit learners.', 'danger')
        return redirect(url_for('logout'))

    learner_ref = db.collection('children').document(learner_id)
    learner = learner_ref.get().to_dict()

    if not learner:
        flash('Learner not found.', 'danger')
        return redirect(url_for('manage_learner'))

    if request.method == 'POST':
        # Update learner data
        name = request.form.get('name')
        surname = request.form.get('surname')
        grade = request.form.get('grade')
        id_number = request.form.get('id_number')
        parent_id = request.form.get('parent_id')

        learner_ref.update({
            'name': name,
            'surname': surname,
            'grade': grade,
            'child_id': id_number,
            'parent_id': parent_id,
        })

        flash('Learner updated successfully!', 'success')
        return redirect(url_for('manage_learner'))

    # Fetch parents for the dropdown list
    parents_query = db.collection('users').where('role', '==', 'Parent').order_by('registered_at', direction=firestore.Query.DESCENDING).stream()
    parents = [{'id': parent.id, **parent.to_dict()} for parent in parents_query]

    return render_template('edit_child.html', learner=learner, learner_id=learner_id, parents=parents)


# Update Security info
@app.route('/edit-security/<security_id>', methods=['GET', 'POST'])
@login_required
def edit_security(security_id):
    # Ensure only Admin can edit
    if current_user.role != 'Admin':
        flash('You are not authorized to edit security personnel.', 'danger')
        return redirect(url_for('logout'))

    security_ref = db.collection('securities').document(security_id)
    security = security_ref.get().to_dict()

    if not security:
        flash('Security personnel not found.', 'danger')
        return redirect(url_for('manage_security'))

    if request.method == 'POST':
        # Update security personnel data
        name = request.form.get('name')
        role = request.form.get('role')
        contact = request.form.get('contact')
        password = request.form.get('password')

        hashed_password = generate_password_hash(password) if password else security.get('password')

        security_ref.update({
            'name': name,
            'role': role,
            'contact': contact,
            'password': hashed_password,
        })

        flash('Security personnel updated successfully!', 'success')
        return redirect(url_for('manage_security'))

    return render_template('edit_security.html', security=security, security_id=security_id)


# Delete Parent
@app.route('/delete-parent/<parent_id>', methods=['POST'])
@login_required
def delete_parent(parent_id):
    # Ensure only Admin can delete
    if current_user.role != 'Admin':
        flash('You are not authorized to delete parents.', 'danger')
        return redirect(url_for('logout'))

    # Delete parent document
    parent_ref = db.collection('users').document(parent_id)
    parent_ref.delete()

    # Delete all associated children
    children_ref = db.collection('children').where('parent_id', '==', parent_id).stream()
    for child in children_ref:
        db.collection('children').document(child.id).delete()

    flash('Parent and their children deleted successfully!', 'success')
    return redirect(url_for('manage_parent'))


# Route to delete a child
@app.route('/delete-child/<child_id>', methods=['POST'])
@login_required
def delete_learner(child_id):
    # Ensure only Admin can delete
    if current_user.role != 'Admin':
        flash('You are not authorized to delete learners.', 'danger')
        return redirect(url_for('logout'))

    learner_ref = db.collection('children').document(child_id)
    learner_ref.delete()

    flash('Learner deleted successfully!', 'success')
    return redirect(url_for('manage_learner'))


# Delete Security
@app.route('/delete-security/<security_id>', methods=['POST'])
@login_required
def delete_security(security_id):
    # Ensure only Admin can delete
    if current_user.role != 'Admin':
        flash('You are not authorized to delete security personnel.', 'danger')
        return redirect(url_for('logout'))

    security_ref = db.collection('securities').document(security_id)
    security_ref.delete()

    flash('Security personnel deleted successfully!', 'success')
    return redirect(url_for('manage_security'))


# --------------------------------------------------------------- MANAGE ROUTES ------------------------------------------------------------


# Helper function to format Firestore timestamps to a readable date format
def format_date(timestamp):
    if isinstance(timestamp, datetime):
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    return 'N/A'  # Return 'N/A' if the timestamp is missing or not a valid datetime

@app.route('/manage-parents')
@login_required
def manage_parent():
    # Check if the user is authorized (optional: can add role-based restrictions)
    if current_user.role != 'Admin':
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('logout'))

    # Query Firestore for users with role 'Parent'
    parents_query = db.collection('users').where('role', '==', 'Parent').stream()
    
    # Process each parent's data and format the registered_at timestamp
    parents = []
    for parent in parents_query:
        parent_data = parent.to_dict()
        parent_data['id'] = parent.id
        
        # Format the 'registered_at' timestamp
        if 'registered_at' in parent_data:
            parent_data['registered_at'] = format_date(parent_data['registered_at'])
        
        parents.append(parent_data)

    # Render the manage parents template with the data
    return render_template('manage_parent.html', parents=parents)


@app.route('/manage-security')
@login_required
def manage_security():
    # Check if the user is authorized (optional: can add role-based restrictions)
    if current_user.role != 'Admin':
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('logout'))

    # Query Firestore for securities collection
    securities_query = db.collection('securities').stream()
    securities = [{'id': security.id, **security.to_dict()} for security in securities_query]

    # Render the manage securities template with the data
    return render_template('manage_security.html', securities=securities)


@app.route('/manage_learner')
def manage_learner():
    # Check if the user is authorized (optional: can add role-based restrictions)
    if current_user.role != 'Admin':
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('logout'))

    # Query Firestore for securities collection
    learner_query = db.collection('children').stream()
    learners = [{'id': child.id, **child.to_dict()} for child in learner_query]

     # Query Firestore for parents collection
    parent_query = db.collection('users').stream()  # Assuming 'users' is the collection name for parents
    parents = {parent.id: parent.to_dict().get('name', 'Unknown') for parent in parent_query}

    # Add parent name to each learner
    for learner in learners:
        learner['parent_name'] = parents.get(learner.get('parent_id'), 'Unknown')

    # Render the manage learners template with the data
    return render_template('manage_learner.html', learners=learners)


# Attendance view of kids for admin
@app.route('/attendance')
def attendance():
    # Ensure the user is a Admin
    if current_user.role != 'Admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))
    
    # Get data from Firestore collections
    children_ref = db.collection('children')
    entrance_ref = db.collection('entrances')
    exit_ref = db.collection('exits')

    children_docs = children_ref.stream()
    entrance_docs = entrance_ref.stream()
    exit_docs = exit_ref.stream()

    # Process the data into a single attendance data structure
    attendance_data = []

    # Convert Firestore documents to dictionaries for easier manipulation
    children = {doc.id: doc.to_dict() for doc in children_docs}
    entrances = {doc.id: doc.to_dict() for doc in entrance_docs}
    exits = {doc.id: doc.to_dict() for doc in exit_docs}

    # Loop through children to create the attendance data
    for child_id, child in children.items():
        child_name = child.get('name')
        child_grade = child.get('grade')

        # Find entrance and exit data for the child
        child_entrance = [e for e in entrances.values() if e.get('child_id') == child_id]
        child_exit = [ex for ex in exits.values() if ex.get('child_id') == child_id]

        # Sort by date (assuming the 'date' field exists in the entrance and exit collections)
        child_entrance.sort(key=lambda x: x.get('date'), reverse=True)
        child_exit.sort(key=lambda x: x.get('date'), reverse=True)

        # Create a list of attendance records
        for entry in child_entrance:
            # For each entrance, try to match an exit record on the same date
            entrance_time = entry.get('time')
            date = entry.get('date')

            exit_time = next((ex.get('time') for ex in child_exit if ex.get('date') == date), None)

            # Add the record to the attendance data
            attendance_data.append({
                'name': child_name,
                'grade': child_grade,
                'date': date,
                'entrance_time': entrance_time,
                'exit_time': exit_time
            })

    # Render the attendance table
    return render_template('attendance.html', attendance_data=attendance_data)


# Route for attendance for logged in Parent
@app.route('/parent-attendance')
@login_required
def parent_attendance():
    # Ensure the user is a parent
    if current_user.role != 'Parent':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('logout'))

    parent_id = current_user.email  # The parent ID is set to the current user's email

    # Query Firestore to get the children associated with the parent
    children_ref = db.collection('children').where('parent_id', '==', parent_id)
    children_docs = children_ref.stream()

    # Query Firestore for entrance and exit data
    entrance_ref = db.collection('entrances')
    exit_ref = db.collection('exits')

    entrance_docs = entrance_ref.stream()
    exit_docs = exit_ref.stream()

    # Process the data into a single attendance data structure
    attendance_data = []

    # Convert Firestore documents to dictionaries for easier manipulation
    children = {doc.id: doc.to_dict() for doc in children_docs}
    entrances = {doc.id: doc.to_dict() for doc in entrance_docs}
    exits = {doc.id: doc.to_dict() for doc in exit_docs}

    # Loop through the parent's children to create the attendance data
    for child_id, child in children.items():
        child_name = child.get('name')
        child_grade = child.get('grade')

        # Find entrance and exit data for the child
        child_entrance = [e for e in entrances.values() if e.get('child_id') == child_id]
        child_exit = [ex for ex in exits.values() if ex.get('child_id') == child_id]

        # Sort by date (assuming the 'date' field exists in the entrance and exit collections)
        child_entrance.sort(key=lambda x: x.get('date'), reverse=True)
        child_exit.sort(key=lambda x: x.get('date'), reverse=True)

        # Create a list of attendance records
        for entry in child_entrance:
            # For each entrance, try to match an exit record on the same date
            entrance_time = entry.get('time')
            date = entry.get('date')

            exit_time = next((ex.get('time') for ex in child_exit if ex.get('date') == date), None)

            # Add the record to the attendance data
            attendance_data.append({
                'name': child_name,
                'grade': child_grade,
                'date': date,
                'entrance_time': entrance_time,
                'exit_time': exit_time
            })

    # Render the attendance table along with parent info
    return render_template('parent_attendance.html', attendance_data=attendance_data)


# View Parent info
@app.route('/view-parent-info/<parent_id>')
@login_required
def view_parent_info(parent_id):
    # Ensure only Admin can view parent information
    if current_user.role != 'Admin':
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('logout'))

    # Fetch parent details from Firestore
    parent_ref = db.collection('users').document(parent_id)
    parent_doc = parent_ref.get()

    if not parent_doc.exists:
        flash('Parent not found.', 'danger')
        return redirect(url_for('manage_parent'))

    parent = parent_doc.to_dict()

    # Fetch all children of the parent
    children_query = db.collection('children').where('parent_id', '==', parent_id).stream()
    children = [{'id': child.id, **child.to_dict()} for child in children_query]

    # Render the template and pass parent and children information
    return render_template('view_parent_info.html', parent=parent, children=children)


@app.route('/children', methods=['GET'])
@login_required
def view_children():
    # Fetch the current parent's ID
    parent_id = current_user.get_id()

    # Query to get all children belonging to this parent from the database (Firestore example)
    children_query = db.collection('children').where('parent_id', '==', parent_id).stream()
    children = [{'id': child.id, **child.to_dict()} for child in children_query]

    # Render the parent dashboard with the children data
    return render_template('view_children.html', children=children)


@app.route('/My Child Info/<parent_id>/<child_id>', methods=['GET'])
@login_required
def view_child_info(parent_id, child_id):
    # Ensure the current user is the parent of this child
    if current_user.get_id() != str(parent_id):
        flash('You are not authorized to view this child\'s information.', 'danger')
        return redirect(url_for('parent_dashboard'))

    # Fetch child info from the database (assuming you're using Firestore or similar)
    child_ref = db.collection('children').document(str(child_id)).get()
    child_data = child_ref.to_dict()

    # Check if the child belongs to the parent
    if not child_data or child_data.get('parent_id') != str(parent_id):
        flash('You are not authorized to view this child\'s information.', 'danger')
        return redirect(url_for('parent_dashboard'))

    # Render the template to show child info
    return render_template('view_child_info.html', child=child_data)

# --------------------------------------------------------- OTHER ROUTES ----------------------------------------------------------------------

@app.route('/entrances')
@login_required
def entrances():
    try:
        # Get exit data
        entrance_ref = db.collection('entrances')
        entrance_docs = entrance_ref.stream()

        entrance_data = []

        # Process entrances
        for doc in entrance_docs:
            entrance = doc.to_dict()
            entrance_data.append({
                'child_name': entrance.get('name', 'Unknown'),  # Provide a default value if key doesn't exist
                'date': entrance.get('date', 'N/A'),                  # Handle missing values
                'entrance_time': entrance.get('time', 'N/A'),
                'entered_by': entrance.get('scanned_by', 'Unknown'),
            })

        # Check if exit_data is empty and handle appropriately
        if not entrance_data:
            flash("No exits found.", "info")  # Flash a message if no exits are available

        return render_template('entrances.html', entrance_data=entrance_data)

    except Exception as e:
        flash(f"Error retrieving entrance data: {str(e)}", "danger")  # Handle errors
        return redirect(url_for('parent_dashboard'))


@app.route('/exits')
@login_required
def exits():
    try:
        # Get exit data
        exit_ref = db.collection('exits')
        exits_docs = exit_ref.stream()

        exit_data = []

        # Process exits
        for doc in exits_docs:
            exit = doc.to_dict()
            exit_data.append({
                'child_name': exit.get('name', 'Unknown'),  # Provide a default value if key doesn't exist
                'date': exit.get('date', 'N/A'),                  # Handle missing values
                'exit_time': exit.get('time', 'N/A'),
                'exited_by': exit.get('scanned_by', 'Unknown'),
            })

        # Check if exit_data is empty and handle appropriately
        if not exit_data:
            flash("No exits found.", "info")  # Flash a message if no exits are available

        return render_template('exits.html', exit_data=exit_data)

    except Exception as e:
        flash(f"Error retrieving exit data: {str(e)}", "danger")  # Handle errors
        return redirect(url_for('parent_dashboard'))


@app.route('/401')
def fourOone():
    return render_template('401.html')

@app.route('/404')
def fourOfour():
    return render_template('404.html')

@app.route('/500')
def fiveOO():
    return render_template('500.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')


@app.route('/generate_alerts', methods=['GET'])
@login_required
def generate_alerts():
    if current_user.role != 'Admin':
        flash('You are not authorized to generate alerts.', 'danger')
        return redirect(url_for('index'))

    # Define the absence criteria: check attendance until 9:00 AM
    current_time = datetime.utcnow()
    cutoff_time = current_time.replace(hour=10, minute=0, second=0, microsecond=0)

    # Get all children
    children_ref = db.collection('children').stream()
    absent_children = []

    for child in children_ref:
        child_data = child.to_dict()
        child_id = child.id

        # Query entrances for today for each child
        entrance_ref = db.collection('entrances').where('child_id', '==', child_id).where('date', '==', current_time.strftime('%Y-%m-%d')).get()

        # If no entrance record exists before cutoff time, mark as absent
        if not entrance_ref:
            absent_children.append(child_data)

            # Create alert for the parent
            alert_data = {
                'child_id': child_id,
                'parent_id': child_data['parent_id'],
                'message': f"Your child, {child_data['name']} {child_data['surname']}, was not checked in today by {cutoff_time.strftime('%H:%M')}. Please confirm if your child is safe.",
                'status': 'pending',
                'created_at': datetime.utcnow(),
            }
            db.collection('alerts').add(alert_data)

    flash(f'Alerts generated for {len(absent_children)} absent children.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/alerts', methods=['GET', 'POST'])
@login_required
def alerts():
    # Ensure that only parents can access this
    if current_user.role != 'Parent':
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('index'))

    parent_id = current_user.get_id()

    # Get alerts for the logged-in parent
    alerts_query = db.collection('alerts').where('parent_id', '==', parent_id).where('status', '==', 'pending').stream()
    alerts = [{'id': alert.id, **alert.to_dict()} for alert in alerts_query]

    if request.method == 'POST':
        alert_id = request.form.get('alert_id')
        response = request.form.get('response')

        # Update the alert in Firestore
        alert_ref = db.collection('alerts').document(alert_id)
        alert_ref.update({
            'status': 'resolved',
            'response': response,
            'responded_at': datetime.utcnow()
        })

        flash('Your response has been recorded. Thank you.', 'success')
        return redirect(url_for('alerts'))

    return render_template('alerts.html', alerts=alerts)


@app.route('/view_alerts_responses', methods=['GET'])
@login_required
def view_alerts_responses():
    # Ensure only Admins can access this page
    if current_user.role != 'Admin':
        flash('You are not authorized to view this page.', 'danger')
        return redirect(url_for('index'))

    # Query Firestore to get all alerts and their responses
    alerts_query = db.collection('alerts').stream()
    alerts_with_responses = []

    for alert in alerts_query:
        alert_data = alert.to_dict()
        alert_data['id'] = alert.id  # Include the document ID
        alerts_with_responses.append(alert_data)

    return render_template('view_alerts_responses.html', alerts=alerts_with_responses)


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')





# Run the app
if __name__ == '__main__':
    app.run(debug=True)