import smtplib
from smtplib import SMTP
from email.message import EmailMessage
def sendmail(to,body,subject):
    server = smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('sudharanikancherla1@gmail.com','xxlq jjcg xaui ucnc')
    #email forward
    msg=EmailMessage()
    msg['FROM']='sudharanikancherla1@gmail.com'
    msg['TO']=to
    msg['SUBJECT']=subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()