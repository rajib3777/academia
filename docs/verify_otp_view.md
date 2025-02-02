This VerifyOTPView handles the verification of OTPs sent to a user's phone number.
It validates the provided phone number and OTP combination and checks the 
status of the OTP (e.g., whether it is expired, already verified, or invalid).

**Authentication and Permissions**:
    - No authentication is required for this endpoint.  
    - No permission classes are enforced.

**HTTP Methods**:
    - `POST`: Validates the OTP provided by the user.

**Workflow**:
    1. Accepts a `phone_number` and `otp` in the request body.  
    2. Validates the incoming data using `VerifyOTPSerializer`.  
    3. Checks for the existence of an `OTPVerification` instance associated with 
       the phone number.  
    4. Performs the following checks:
       - If the phone number is already verified, returns an error response.  
       - If the OTP has expired, returns an error response.  
       - If the OTP matches the stored OTP, marks the phone number as verified 
         and returns a success response.  
       - If the OTP does not match, returns an error response.  
    5. Handles cases where the phone number or OTP is invalid.  

**Request Body**:
    - `phone_number` (str): The phone number associated with the OTP.
    - `otp` (str): The one-time password sent to the phone number.

**Responses**:
    - `200 OK`: OTP verified successfully.
    - `400 Bad Request`: Invalid data, expired OTP, or phone number not found.
    - `404 Not Found`: OTPVerification instance does not exist for the given phone number.

**Example Request**:
```json
{
    "phone_number": "+1234567890",
    "otp": "123456"
}
```

**Example Responses**:
- Success:
    ```json
    {
        "message": "OTP verified successfully."
    }
    ```
- Errors:
    - Phone number already verified:
        ```json
        {
            "error": "Phone number already verified."
        }
        ```
    - OTP expired:
        ```json
        {
            "error": "OTP has expired."
        }
        ```
    - Invalid OTP:
        ```json
        {
            "error": "Invalid OTP."
        }
        ```
    - Invalid phone number:
        ```json
        {
            "error": "Invalid phone number."
        }
    ```