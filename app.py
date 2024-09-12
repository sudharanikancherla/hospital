from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file
from flask_session import Session
import mysql.connector
from otp import genotp
from cmail import sendmail
from key import secret_key
from doctoken import token,dtoken
from io import BytesIO
import re
import flask_excel as excel
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
excel.init_excel(app)
Session(app)
mydb=mysql.connector.connect(host='localhost',user='root',password='Admin',db='mra')
app.secret_key=b"'N\xedI\x9f"
@app.route('/')
def welcome():
    return render_template('/welcome.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        Doctor_id=request.form['D_id']
        Doctor_name=request.form['D_name']
        email=request.form['email']
        password=request.form['password']
        print(Doctor_id,Doctor_name,email,password)
        #mysql connection
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select  count(email) from doctor where email=%s',[email])
        data=cursor.fetchone()[0]
        if data == 0:
             otp=genotp()
             print(otp)
             data={'otp':otp,'email':email,'D_id':Doctor_id,'D_name':Doctor_name,'password':password}
             subject='Verification otp for MR Application'
             body=f'Registration otp for Medical records Application {otp}'
             sendmail(to=email,subject=subject,body=body)
             return redirect(url_for('verifyotp',data1=token(data=data)))
        else:
            flash('Email Already existed')
            return redirect(url_for('register'))
        #mysql connection
    return render_template('register.html')
#otp generation
@app.route('/otp/<data1>',methods=['GET','POST'])
def verifyotp(data1):
    try:
        data1=dtoken(data=data1)
    except Exception as e:
         print(e)
         return 'time out of otp'
    else:
        
        if request.method=="POST":
            dotp=request.form['otp']
            print('hi')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into doctor(email,D_id,D_name,password) values(%s,%s,%s,%s)',
            [data1['email'],data1['D_id'],data1['D_name'],data1['password']])
            mydb.commit()
            cursor.close()
            flash(f'Signin successfully')
            return redirect(url_for('login'))
        else:
            return f'otp invalid check your email.'
    finally:
        print('Done')
        return render_template('otp.html')
#login page
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('email'):
        return redirect(url_for('patient'))
    else:
        if request.method=='POST':
            email=request.form['email']
            password=request.form['password']
            print(password)
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select email,password from doctor where email=%s',[email])
                data=cursor.fetchone()
                print(data[1].decode('utf-8'))
            except Exception as e:
                print(e)
                return 'email incorrect'
            else:
                print('hi')
                if data[1].decode('utf-8')==password:
                    
                    session['email']=email
                    if not session.get(email):
                        session[email]={}
                    return redirect(url_for('patient'))
                else:
                    flash('invaild password')
        return render_template('login.html')
@app.route('/patient')
def patient():
    if not session.get('email'):
        return redirect(url_for('login'))
    return render_template('patient.html')

@app.route('/addnotes',methods=['GET','POST'])
def addnotes():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            p_id=request.form['p_id']
            p_name=request.form['p_name']
            gender=request.form['gender']
            age=request.form['age']
            email=request.form['email']
            disease=request.form['disease']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into patient(p_id,p_name,gender,age,email,disease) values(%s,%s,%s,%s,%s,%s)',[p_id,p_name,gender,age,email,disease])
            mydb.commit()
            cursor.close()
            flash('f Notes {patient} added successfully.')
            return redirect(url_for('patient'))
    return render_template('patientnote.html')

@app.route('/allpatientnote')
def allpatientnote():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        added_by=session.get('email')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select p_id,p_name,gender,age,email from patient where email=%s',[added_by])
        data=cursor.fetchall()
        print(data)
        return render_template('viewallnote.html',data=data)
@app.route('/viewnote/<p_id>')
def viewnote(p_id):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select p_id,p_name,gender,age,email,disease from patient where email=%s and p_id=%s',[session.get('email'),p_id])
        note_data=cursor.fetchone()
        return render_template('viewnote.html',note_data=note_data)
@app.route('/updatenote/<p_id>',methods=['GET','POST'])
def updatenote(p_id):
     if not session.get('email'):
         return redirect(url_for('login'))
     else:
         cursor=mydb.cursor(buffered=True)
         cursor.execute('select p_id,p_name,gender,age,email,disease from patient where p_id=%s',[p_id])
         note_data=cursor.fetchone()
         if request.method=='POST':
            
             p_name=request.form['p_name']
             gender=request.form['gender']
             age=request.form['age']
             email=request.form['email']
             disease=request.form['disease']            
             cursor.execute('update patient set p_name=%s,gender=%s,age=%s,email=%s,disease=%s where email=%s and p_id=%s',
             [p_name,gender,age,email,disease,session.get('email'),p_id])
             mydb.commit()
             cursor.close()
             flash(f'notes of {p_name} updated successfully')
             return redirect(url_for('updatenote',p_id=p_id))
     return render_template('updatenote.html',note_data=note_data)

@app.route('/deletenote/<p_id>',methods=['GET','POST'])
def deletenote(p_id):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete  from patient where p_id=%s and email=%s',[p_id,session.get('email')])
        mydb.commit()
        cursor.close()
        flash(f'Note  {p_id} deleted successfully')
        return redirect(url_for('patient'))

@app.route('/logout')
def logout():
    if session.get('email'):
        session.pop('email')
        return redirect('login')
    else:
        return redirect('login')
@app.route('/forgot_password',methods=['GET','POST'])
def forgotpassword():
    if session.get('email'):
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            email=request.form['email']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(email) from doctor where email=%s',[email])
            count=cursor.fetchone()[0] 
            if count==0:
                falsh('Email not exists pls register.')
                return redirect(url_for('register'))
            elif count==1:
                subject='Reset link for hospital Application'
                body=f"Reset link for hospital application: {url_for('reset',data=token(data=email),_external=True)}"
                sendmail(to=email,subject=subject,body=body)
                flash('Reset link has been sent to given Email.')
            else:
                return 'something went wrong'
        return render_template('forgotpassword.html')
@app.route('/reset/<data>',methods=['GET','POST'])
def reset(data):
    try:
        email=dtoken(data=data)
    except Exception as e:
        print(e)
        return 'Something went wrong'
    else:
        if request.method=='POST':
            npassword=request.form['npassword']
            cpassword=request.form['cpassword']
            if npassword==cpassword:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update doctor set password=%s where email=%s',[npassword,email])
                mydb.commit()
                cursor.close()
                flash('Newpassword updated successfully')
                return redirect(url_for('login'))
            else:
                return'confirmation password wrong'
        return render_template('newpassword.html')
@app.route('/fileupload',methods=['GET','POST'])
def fileupload():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select p_id,p_name from patient where email=%s',[session.get('email')])
        data=cursor.fetchall()
        print(data)
        if request.method=='POST':
            patient_id=request.form.get('p_id')
            file=request.files.get('f_id')
            file_name=file.filename
            email=session.get('email')
            
            file_data=file.read()
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into files(patient_id,file_name,file_data,email) values(%s,%s,%s,%s)',
            [patient_id,file_name,file_data,email])
            mydb.commit()
            cursor.close()
            flash(f'file {file.filename} added successfully')
            return redirect(url_for('patient'))
    
    return render_template('fileupload.html',data=data)
@app.route('/viewall_files')
def viewall_files():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        email=session.get('email')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select f_id,patient_id,file_name,email,uploaded_at from files where email=%s',
        [email])
        data=cursor.fetchall()
        return render_template('viewallfiles.html',data=data)
@app.route('/view_file/<f_id>')
def view_file(f_id):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        try:
           cursor=mydb.cursor(buffered=True)
           cursor.execute('select file_name,file_data from files where f_id=%s and email=%s',
           [f_id,session.get('email')])
           fname,fdata=cursor.fetchone()
           bytes_data=BytesIO(fdata)
           filename=fname
           return send_file(bytes_data,download_name=filename,as_attachment=False)
        except Exception as e:
            print(e)
            return 'file not found'
        finally:
            cursor.close()
@app.route('/download_file/<f_id>')
def download_file(f_id):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        try:
           cursor=mydb.cursor(buffered=True)
           cursor.execute('select file_name,file_data from files where f_id=%s and email=%s',
           [f_id,session.get('email')])
           fname,fdata=cursor.fetchone()
           bytes_data=BytesIO(fdata)
           filename=fname
           return send_file(bytes_data,download_name=filename,as_attachment=True)
        except Exception as e:
            print(e)
            return 'file not found'
        finally:
            cursor.close()
@app.route('/delete_file/<f_id>')
def delete_file(f_id):
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from files where f_id=%s and email=%s',[f_id,session.get('email')])
        mydb.commit()
        cursor.close()
        flash(f' file {f_id} deleted successfully')  
        return redirect(url_for('patient'))  
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('email'):
        if request.method=='POST':
            name=request.form['sname']
            strg=['A-Za-z0-9']
            pattern=re.compile(f'^{strg}',re.IGNORECASE)
            if (pattern.match(name)):
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select * from patient where email=%s and p_name LIKE %s',[session.get('email'),name+'%'])
                sname=cursor.fetchall()
                cursor.execute('select f_id,patient_id,file_name,email,uploaded_at from files where email=%s and file_name LIKE %s',[session.get('email'),name+'%'])
                fname=cursor.fetchall()
                cursor.close()
                print(fname)
                print(sname)
                return render_template('patient.html',sname=sname,fname=fname) 
            else:
                flash('result not found')
                return redirect(url_for('patient'))
    return redirect(url_for('login'))
        

@app.route('/getexcel_data')
def getexcel_data():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        user=session.get('email')
        columns=['p_id','p_name','gender','age','email','disease']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select p_id,p_name,gender,age,email,disease from patient where email=%s',[user])
        print(user)
        data=cursor.fetchall()
        array_data=[list (i) for i in data]
        array_data.insert(0,columns)
        return excel.make_response_from_array(array_data,'xlsx',filename='Notedata')               
#appoinment route
@app.route('/appointment/new', methods=['GET', 'POST'])
def new_appointment():
    if session.get('email'):
        if request.method == 'POST':
            apt_id=request.form['apt_id']
            patient_id = request.form['patient_id']
            apt_date = request.form['apt_date']
            apt_time = request.form['apt_time']
            apt_reason = request.form['apt_reason']
            status=request.form['status']
            email=request.form['email']
            try:
                cursor = mydb.cursor(buffered=True)
                cursor.execute('''insert into appointment(apt_id,email, patient_id, apt_date, apt_time, apt_reason,status)
                values(%s, %s, %s, %s, %s,%s,%s)''',[apt_id,session.get('email'), patient_id, apt_date, apt_time, apt_reason,status])
                mydb.commit()
                cursor.close()
                flash('Appointment scheduled successfully!')
                return redirect(url_for('view_appointment'))
            except Exception as e:
                cursor.close()
                flash('Error scheduling appointment. Please try again.')
                print(f"Database error: {e}")
                return redirect(url_for('new_appointment'))
        return render_template('new_appointment.html')
    return redirect(url_for('login'))
@app.route('/viewappointment', methods=['GET'])
def view_appointment():
    if session.get('email'):
        cursor = mydb.cursor(buffered=True)
        cursor.execute('select * from appointment where email=%s order by apt_date, apt_time',[session.get('email')])
        appointment_data=cursor.fetchall()
        cursor.close()
        return render_template('view_appointment.html', appointment_data=appointment_data)
        cursor.close()
        flash('Error fetching appointments.')
        return redirect(url_for('patient'))
    return redirect(url_for('login'))
@app.route('/update_appointment/<int:apt_id>', methods=['GET', 'POST'])
def update_appointment(apt_id):
    if session.get('email'):
        if request.method == 'POST':
            apt_date = request.form['apt_date']
            apt_time = request.form['apt_time']
            apt_reason = request.form['apt_reason']
            status = request.form['status']
            cursor = mydb.cursor(buffered=True)
            cursor.execute('update appointment set apt_date=%s,apt_time=%s,apt_reason=%s,status=%s,updated_at=current_timestamp where apt_id=%s and email=%s', [apt_date, apt_time, apt_reason, status, apt_id, session.get('email')])
            mydb.commit()
            cursor.close()
            flash(f'Appointment updated successfully!')
            return redirect(url_for('view_appointment'))
            cursor.close()
            flash(f'Error updating appointment.')
            return redirect(url_for('update_appointment', apt_id=apt_id))
        
        try:
            cursor = mydb.cursor(buffered=True)
            cursor.execute('select * from appointment where apt_id=%s and email=%s',[apt_id, session.get('email')])
            appointment=cursor.fetchone()
            print(appointment)
            cursor.close()
            if appointment:
                return render_template('update_appointment.html', appointment=appointment)
            else:
                flash('Appointment not found.')
                return redirect(url_for('view_appointment'))
        except Exception as e:
            print(e)
            flash('Wrong appointment details.')
            return redirect(url_for('view_appointment'))
    return redirect(url_for('login'))
@app.route('/surgery',methods=['GET','POST'])
def surgery():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            try:
                sur_id=request.form['sur_id']
                email=request.form['email']
                p_id=request.form['p_id']
                sur_date=request.form['sur_date']
                sur_time=request.form['sur_time']
                surgery_type=request.form['surgery_type']
                status=request.form['status']
                notes=request.form['notes']
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into surgery(sur_id,email,p_id,sur_date,sur_time,surgery_type,status,notes) values(%s,%s,%s,%s,%s,%s,%s,%s)',[sur_id,email,p_id,sur_date,sur_time,surgery_type,status,notes])
                mydb.commit()
                cursor.close()
                print(request.form)
                flash(f'Surgery {sur_id} added successfully.')
                return redirect(url_for('patient'))
            except Exception as e:
                print(f"An error occurred: {e}")
                flash('Please add notes of the patient first while adding the surgery.')
            return redirect(url_for('surgery'))
    
    return render_template('surgery.html')

            

@app.route('/allsurgeries')
def allsurgeries():
    if not session.get('email'):
        return redirect(url_for('login'))
    else:
        email=session.get('email')
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select sur_id,email,p_id,sur_date,sur_time,surgery_type,status,notes from surgery where email=%s',[email])
        data=cursor.fetchall()
        print(data)
        return render_template('allsurgeries.html',data=data)





app.run(debug=True,use_reloader=True)