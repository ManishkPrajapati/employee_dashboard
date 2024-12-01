from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Note
from . import db, employees, department
import json

views = Blueprint('views', __name__)



@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    all_employees = list(employees.find())
    return render_template("home.html", emp = all_employees, user= current_user)


@views.route('/update_employee/<string:unique_id>', methods=['GET', 'POST'])
@login_required
def update_employee(unique_id):
    employee = employees.find_one({"unique_id": unique_id})
    
    all_departments = [dept['name'] for dept in department.find()]

    if request.method == 'POST':
        new_email = request.form.get('email', employee['email'])
        selected_departments = request.form.getlist('departments')  
        
        if new_email != employee['email']:
            employee['email'] = new_email
        
        if selected_departments != employee['departments']:
            employee['departments'] = selected_departments

        employees.update_one({"unique_id": unique_id}, {"$set": employee})

        flash('Employee updated successfully!', category='success')
        return redirect(url_for('views.home'))

    return render_template("update_employee.html", employee=employee, all_departments=all_departments, user = current_user)



@views.route('/departments')
def manage_departments():
    departments = department.find()
    return render_template('departments.html', departments=departments, user = current_user)

@views.route('/edit_department/<department_id>', methods=['GET', 'POST'])
def edit_department(department_id):
    dept = department.find_one({"unique_id": department_id})
    
    if request.method == 'POST':
        new_name = request.form.get('name')
        
        if new_name:
            department.update_one({"unique_id": department_id}, {"$set": {"name": new_name}})
            flash('Department name updated successfully!', category='success')
            return redirect(url_for('views.manage_departments')) 
        else:
            flash('Department name cannot be empty!', category='error')

    return render_template('edit_department.html', department=dept, user=current_user)
