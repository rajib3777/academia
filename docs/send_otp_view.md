This SendOTPView handles the generation and sending of a One-Time Password (OTP) 
to the specified phone number provided in the request. It uses the `SendOTPSerializer`
for input validation and ensures that an OTP is either created or updated for the phone number.

Methods:  
    - post(request, *args, **kwargs): Handles the creation and sending of OTP.

Attributes:  
    - permission_classes (tuple): No authentication or permission is required for this endpoint.  
    - authentication_classes (tuple): No authentication classes are used for this endpoint.

Workflow:
    1. The user submits a POST request with a phone number in the request body.  
    2. The request data is validated using `SendOTPSerializer`.  
    3. A new OTP is generated using the `generate_otp` function.  
    4. The OTP is saved or updated in the `OTPVerification` model with `is_verified` set to False.  
    5. The OTP is sent to the phone number via SMS using the `send_sms` function.  
    6. Returns a success response if the OTP is sent successfully.  
    7. Returns an error response if the SMS fails to send or if there are validation errors.  

Responses:
    - 200: {"message": "OTP sent successfully."} if the OTP is sent successfully.  
    - 400: {'error': 'Something wrong! OTP can not send.'} if the SMS fails to send.  
    - 400: {'error': 'Something wrong! OTP can not create.'} if the OTP record cannot be created or updated.  
    - 400: Validation errors if the input data is invalid.  

**Example Request**:
- POST /api/send-otp/
    ```json
    {
        "phone_number": "+8801234567890"
    }
    ```
**Example Responses**:
- Success:
    ```json
    {
        "message": "OTP sent successfully."
    }
    ```

- Errors:
      - SMS Failure:
     ```json
       {
           "error": "Something wrong! OTP can not send."
       }
     ```
     - OTP Creation Failure:
    ```json
      {
           "error": "Something wrong! OTP can not create."
      }
    ```
    - Validation Error:
    ```json
    {
       "phone_number": ["This field is required."]
    }
    ```