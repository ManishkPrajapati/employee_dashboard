from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, Response
from flask_login import login_required, current_user
from . import employees, department,user_unique_groups
import json
from datetime import datetime, timedelta
import mysec
import pytz
import requests

views = Blueprint('views', __name__)

facebook_url = mysec.FACEBOOK_URL
facebook_headers = mysec.FACEBOOK_HEADERS

tz = pytz.timezone('Asia/Kolkata')  # Set the timezone


@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
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




@views.route('/webhook', methods=['POST', 'GET'])
def whatsappWebhook():
    if request.method == "GET":
        return Response(request.args.get('challenge'), status=200)

    if request.method == 'POST':
        json_data = request.get_json()

        try:
            json_data['entry'][0]['changes'][0]['value']['statuses']
        except KeyError:
            if json_data.get('object') == "whatsapp_business_account" and json_data.get('entry')[0].get('changes')[0].get('value').get('contacts') is not None:
                pass
            else:
                return Response(status=200)

        if json_data.get('entry'):
            try:
                contact_number = str(json_data['entry'][0]['changes'][0]['value']['messages'][0]['from'])
            except:
                return Response(status=200)

            user_unique_group_obj = user_unique_groups.find_one({'contact_number': contact_number})

            msg_type = json_data['entry'][0]['changes'][0]['value']['messages'][0]['type']

            if msg_type == 'text':
                message_text = json_data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].lower()

                if message_text == "emp":
                    if user_unique_group_obj is not None and user_unique_group_obj.get('chat_bot_flow_completed') == True:
                        send_change_option(contact_number)

                    elif user_unique_group_obj is None or user_unique_group_obj.get('flow_step') == 1:
                        send_text_message(contact_number, "Welcome! Let's start. Here's the list of employees.")
                        employees_list = list(employees.find())
                        employee_names = [emp["name"] for emp in employees_list]
                        print(employee_names)
                        send_list(contact_number, employee_names)
                        user_unique_groups.update_one(
                            {"contact_number": contact_number}, 
                            {"$set": {
                                "flow_step": 1,
                                "chat_bot_flow_completed": False,
                                "updated_time": datetime.now(tz=tz)
                            }},
                            upsert=True
                        )
                        return jsonify({"success": True}), 200

            elif msg_type == 'interactive':
                interactive_type = json_data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['type']
                if interactive_type == 'list_reply':
                    selected_option = json_data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['list_reply']['title']

                    if user_unique_group_obj.get('flow_step') == 1:
                        dept = employees.find_one({'name': selected_option})
                        departments = dept.get('departments', [])
                        send_list(contact_number, departments)
                        user_unique_groups.update_one(
                            {"_id": user_unique_group_obj['_id']},
                            {
                                "$set": {
                                    "flow_step": 2,
                                    "updated_time": datetime.now(tz=tz),
                                    "Employee_name": selected_option
                                }
                            }
                        )
                        return jsonify({"success": True}), 200

                    elif user_unique_group_obj.get('flow_step') == 2:
                        msg = "Thanks you for your selection"
                        send_text_message(contact_number, msg)
                        user_unique_groups.update_one(
                            {"_id": user_unique_group_obj['_id']},
                            {
                                "$set": {
                                    "updated_time": datetime.now(tz=tz),
                                    "chat_bot_flow_completed": True,
                                    "Department": selected_option
                                }
                            }
                        )
                        return jsonify({"success": True}), 200

                elif interactive_type == 'button_reply':
                    button_id = json_data['entry'][0]['changes'][0]['value']['messages'][0]['interactive']['button_reply']['id']
                    if button_id == 'yes_change_option':
                        msg = f"Hello! You selected the following details:\n\n Employee: {user_unique_group_obj.get('Employee_name')}\n Department: {user_unique_group_obj.get('Department')}\n Selected on: {user_unique_group_obj.get('updated_time')}"
                        send_text_message(contact_number, msg)
                        return jsonify({"success": True}), 200

                    elif button_id == 'no_continue_option':
                        user_unique_groups.delete_one({"_id": user_unique_group_obj['_id']})
                        send_text_message(contact_number, "Please send 'emp' text to start selection again")
                        return jsonify({"success": True}), 200

    return Response(request.args.get('challenge'), status=200)


def send_text_message(contact_number, msg):
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{contact_number}",
        "type": "text",
        "text": {
            "preview_url": False,
            "body": f"{msg}"
        }
    })
    response = requests.request("POST", facebook_url, headers=facebook_headers, data=payload)
    print(response.json())
    return response.json()


def send_list(contact_number, emp):

    sections = [{
        "title": "Employee List",
        "rows": [{"id": employee, "title": employee} for employee in emp]
    }]

    payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{contact_number}",
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Select Employee"
            },
            "body": {
                "text": "Please select employee:"
            },
            "footer": {
                "text": "Scroll to see more options"
            },
            "action": {
                "button": "Choose",
                "sections": sections
            }
        }
    })

    response = requests.post(facebook_url, headers=facebook_headers, data=payload)
    print(response.json())


def send_change_option(contact_number):
    prompt_text = "Do you want to see your last selection"

    payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{contact_number}",
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": prompt_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "yes_change_option",
                            "title": "Yes"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "no_continue_option",
                            "title": "No"
                        }
                    }
                ]
            }
        }
    })
    
    # Send the request
    response = requests.post(facebook_url, headers=facebook_headers, data=payload)
    print(response.json())
    return response.json()



def send_list(contact_number, dept):

    sections = [{
        "title": "Department List",
        "rows": [{"id": dept, "title": department} for department in dept]
    }]

    payload = json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{contact_number}",
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {
                "type": "text",
                "text": "Select Department"
            },
            "body": {
                "text": "Please select department:"
            },
            "footer": {
                "text": "Scroll to see more options"
            },
            "action": {
                "button": "Choose",
                "sections": sections
            }
        }
    })

    response = requests.post(facebook_url, headers=facebook_headers, data=payload)
    print(response.json())