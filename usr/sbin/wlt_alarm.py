def alarm_email(SERVER,USER,PASSWORT,FROM,TO,SUBJECT,MESSAGE):
    logger.info('Send mail!')
    from smtplib import SMTP as smtp
    from email.mime.text import MIMEText as text

    s = smtp(SERVER)

    s.login(USER,PASSWORT)

    m = text(MESSAGE)

    m['Subject'] = SUBJECT
    m['From'] = FROM
    m['To'] = TO


    s.sendmail(FROM,TO, m.as_string())
    s.quit()