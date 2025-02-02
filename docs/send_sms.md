
Sends an SMS message to a specified phone number and logs the SMS history.

This function sends an SMS via a third-party SMS gateway, logs the request in the `SMSHistory` model,
and handles responses to determine the success or failure of the SMS delivery. It updates the status of
the SMS in the history model accordingly.

Parameters:  
    phone_number (str): The recipient's phone number to which the SMS will be sent.  
    message (str): The message content that will be sent in the SMS.  
    sms_type (str): The type of SMS being sent (e.g., OTP, promotional, etc.).  

Returns:  
    bool:   
        - True if the SMS is sent successfully (response code 202).  
        - False if there is an error in sending the SMS or if the response code is not 202.  

Raises:  
    requests.RequestException: If there is a network or request-related issue while communicating with the SMS gateway.  

Workflow:  
    1. A new `SMSHistory` record is created with the phone number, message, and SMS type.  
    2. The function sends the SMS via the third-party SMS gateway using an HTTP POST request.  
    3. The function checks the response code from the gateway:  
        - If the response code is 202 (successful), the `SMSHistory` status is updated to "SENT".  
        - If the response code is not 202 or if an error occurs, the status is updated to "FAILED" and the failure reason is logged.  
    4. If the SMS request fails (e.g., response code is not 202 or exception occurs), the function returns False.  
    5. If the SMS is successfully sent, the function returns True.  

Example:  
    send_sms("+8801234567890", "Your OTP is 123456", "OTP")  

Responses:  
    - 202: SMS sent successfully. The status in `SMSHistory` is updated to "SENT".  
    - Other response codes: SMS failed. The status in `SMSHistory` is updated to "FAILED", and the reason is logged.  
    - RequestException: If there is a network error or problem communicating with the SMS gateway.  
