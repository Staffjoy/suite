# IVR

The Interactive Virtual Receptionist for Staffjoy's phone numbers. 

For now this is a dumb system, but in the future we can make it more advanced by identifying who is calling in. 


## Phone Numbers

For the latest numbers, please view `config.py`.

Here our our USA numbers:

Dev - (630) 733-8569 (DEVJOY)

Stage - 240-837-8243 (STAGE)

Prod - (443) 578-3359 (STFFJY)


On dev, inbound will not work unless you make some changes!

## Adding a new number

We currently only support one number per country code. 

1. Buy a number in a new country code

2. Register callbacks:

    * calls to `http(s)://(www).staffjoy.com/api/ivr/` 
    * sms to `http(s)://(www).staffjoy.com/api/ivr/sms/`

3. Add the phone number to `config.py` in the correct environment

4. Add the country code to `app.constants.PHONE_COUNTRY_CODE_TO_COUNTRY`



