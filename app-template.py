from openai import OpenAI
import os
import streamlit as st
from dotenv import load_dotenv
 
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
 
if openai_api_key is None:
    raise ValueError("OPENAI_API_KEY environment variable not found.")
 
OpenAI.api_key = openai_api_key
client = OpenAI()
    
system_instruction = """
You are an HR assistant. Your task is to help with writing a template for an email so recruiter can reach out to some candidates.
The person who is writing the email is the HR manager of the company. The email should be written in a professional manner.
The person who is writing is {PERSON_NAME} working for {COMPANY_NAME}. The company is a {COMPANY_DESCRIPTION}.
Here is the position description: {JOB_DESCRIPTION}.
Max number of characters in the message: {MAX_MESSAGE_LENGTH}. Of course you can write a shorter message.
The message should be written in the format: {FORMAT}.
Also, the message should be written in the language: {LANG_OPTION}.

The user won't provide the cv of the candidate you want to reach out to, so the message must be universal, only containing some tags.

The output MUST be only the message that the HR manager will send to the candidate.
(You can ignore the email subject and anything below the message).

AS I SAID NO PLACEHOLDERS: NO STUFF LIKE THIS EITHER [LinkedIn Profile: https://me.linkedin.com/in/ognjen]
ONLY PLACEHOLDER TAGS THAT ARE ALLOWED ARE: [fullName], [firstName], [lastName], [location], [jobTitle], [company], [emails]

From above you can see the tags that are allowed, but user will select only some of them and those MUST BE INCLUDED in the message AND NOTHING ELSE.

IMPORTANT: ALL TAGS ARE RELATED TO THE CANDIDATE, NOT TO THE RECRUITER (SENDER OF THE MESSAGE). ALL TAGS ARE RELATED TO RECEIVER OF THE MESSAGE, NOT TO SENDER!!!!!!! EXAMPLE, LOCATION IS NOT THE RECRUITER LOCATION, BUT THE CANDIDATE LOCATION. ETC.

IMPORTANT IMPORTANT!!!: If the user do not provide firstName, or lastName, or fullName, you start the message with Hi, or Hello, or Dear, NOT with Hello [jobTitle] or similar nonsenses. Template must be very clean and clear and not to contain any nonsenses. Example: Hello [jobTitle], THAT IS NONSENSE!!! Hello [company], THAT IS NONSENSE!!! etc. IT IS IMPORTANT THAT YOU FOLLOW THIS INSTRUCTION. THIS IS ALSO NONSENSE Dear [company] Candidate, ONLY USE FIRST NAME OR LAST NAME OR FULL NAME IN STARTING THE MESSAGE. IF THEY ARE NOT PROVIDED AS TAGS, THEN YOU CANNOT USE THEM IN THE MESSAGE, AND START IT ONLY WITH Hi, Hello, Dear, etc. THIS IS ALSO NONSENSE Hello [location] professional. FOLLOW THIS INSTRUCTION!!! DO NOT BREAK IT. IN GREETING ONLY FIRST NAME OR LAST NAME OR FULL NAME COULD BE INCLUDED AND ONLY IF USER PROVIDES THAT TAGS!!!

IMPORTANT: TAGS ARE RELATED TO THE CANDIDATE, NOT TO THE RECRUITER (SENDER OF THE MESSAGE). ALL TAGS ARE RELATED TO RECEIVER OF THE MESSAGE, NOT TO SENDER!!!!!!! EXAMPLE, LOCATION IS NOT THE RECRUITER LOCATION, BUT THE CANDIDATE LOCATION. ETC. YOU CANNOT SAY AT [COMPANY] WE VALUE ETC AS IT IS NOT YOUR COMPANY!!! THAT IS FOR ALL TAGS!!!

YOU CANNOT GENERATE MESSAGE WITHOUT TAGS THAT USER SELECTED. THEY MUST EXIST IN THE MESSAGE. Double check that you use all tags that user selected.
"""

refinement_prompt = """
You are an HR assistant. Your task is to help with writing a message.
Here is the message:
{MESSAGE}
Please refine the message to make it more {REFINEMENT} - {REFINEMENT_DESC}.

The output MUST be only the message that the HR manager will send to the candidate. 
NO SUBJECT OR ANY OTHER TEXT SHOULD BE INCLUDED.

AS I SAID NO PLACEHOLDERS: NO STUFF LIKE THIS EITHER [LinkedIn Profile: https://me.linkedin.com/in/ognjen]
ONLY PLACEHOLDER TAGS THAT ARE ALLOWED ARE: [fullName], [firstName], [lastName], [location], [jobTitle], [company], [emails]

IMPORTANT: ALL TAGS ARE RELATED TO THE CANDIDATE, NOT TO THE RECRUITER (SENDER OF THE MESSAGE). ALL TAGS ARE RELATED TO RECEIVER OF THE MESSAGE, NOT TO SENDER!!!!!!! EXAMPLE, LOCATION IS NOT THE RECRUITER LOCATION, BUT THE CANDIDATE LOCATION. ETC.

IMPORTANT IMPORTANT!!!: If the user do not provide firstName, or lastName, or fullName, you start the message with Hi, or Hello, or Dear, NOT with Hello [jobTitle] or similar nonsenses. Template must be very clean and clear and not to contain any nonsenses. Example: Hello [jobTitle], THAT IS NONSENSE!!! Hello [company], THAT IS NONSENSE!!! etc. IT IS IMPORTANT THAT YOU FOLLOW THIS INSTRUCTION. THIS IS ALSO NONSENSE Dear [company] Candidate, ONLY USE FIRST NAME OR LAST NAME OR FULL NAME IN STARTING THE MESSAGE. IF THEY ARE NOT PROVIDED AS TAGS, THEN YOU CANNOT USE THEM IN THE MESSAGE, AND START IT ONLY WITH Hi, Hello, Dear, etc. THIS IS ALSO NONSENSE Hello [location] professional. FOLLOW THIS INSTRUCTION!!! DO NOT BREAK IT. IN GREETING ONLY FIRST NAME OR LAST NAME OR FULL NAME COULD BE INCLUDED AND ONLY IF USER PROVIDES THAT TAGS!!!

You can only use the tags that are provided in the original message template that user selected.

IMPORTANT: TAGS ARE RELATED TO THE CANDIDATE, NOT TO THE RECRUITER (SENDER OF THE MESSAGE). ALL TAGS ARE RELATED TO RECEIVER OF THE MESSAGE, NOT TO SENDER!!!!!!! EXAMPLE, LOCATION IS NOT THE RECRUITER LOCATION, BUT THE CANDIDATE LOCATION. ETC. YOU CANNOT SAY AT [COMPANY] WE VALUE ETC AS IT IS NOT YOUR COMPANY!!! THAT IS FOR ALL TAGS!!!

YOU CANNOT GENERATE MESSAGE WITHOUT TAGS THAT USER SELECTED. THEY MUST EXIST IN THE MESSAGE. Double check that you use all tags that user selected.

""" 

REFINEMENTS = {
    "Casual": "A relaxed and friendly tone to make the recipient feel at ease. Great for breaking the ice or when communicating in a less formal context.",
    "Formal": "Professional and respectful tone, suitable for communicating in a business setting or when addressing individuals in senior positions.",
    "Personal": "Tailored specifically to the recipient by incorporating personal details, such as past experiences or shared connections, to make the message more relatable.",
    "Positive": "Emphasizes optimism and enthusiasm, aiming to create a motivating and encouraging tone that inspires action or engagement.",
    "Inclusive": "Focuses on making everyone feel valued, regardless of their background, using gender-neutral and diversity-friendly language to foster a sense of belonging.",
    "Shorter": "A more concise and to-the-point message, often necessary when brevity is key, such as when the recipient is busy or there are word-count limitations.",
    "Longer": "A more detailed and comprehensive message, providing additional context or information. Ideal when explaining complex topics, giving background on the company, or when more depth is needed to convey the message effectively.",
    "Initial Contact": "A message tailored for the first outreach.",
    "Follow-Up": "Slightly more persistent but respectful tone and structure.",
    "Final Reminder": "Polite but firm messaging for closing out the outreach process.",
    "Persuasive": "Tailored to encourage the candidate to engage or take action, ideal for convincing passive candidates to respond.",
    "Call to Action Focus": "Emphasize the action part of the message (e.g., scheduling a call, asking for a resume) to ensure it's clear and compelling.",
    "Storytelling": "Format the message with a narrative structure, which could resonate with candidates by telling a story about the company, role, or success stories within the team."
}



def check_credentials(username, password):
    correct_password = os.getenv('USER_PASSWORD')
    return username == "talentwunder" and password == correct_password
 
                
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
 
# Function to display the login form
def display_login_form():
    st.title("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")
        if login_button:
            if check_credentials(username, password):
                st.session_state.logged_in = True
                st.success("Logged in successfully.")
                st.rerun()
            else:
                st.error("Incorrect username or password.")
                
def data_extraction(prompt, mandatory_tags):
    completion = client.chat.completions.create(
                  model='gpt-4o',
                  temperature=0.9,
                  messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f'Generate me a template for a linkedin message to reach out to a candidate. The only tags that can be in the message are: {mandatory_tags}'}
                ])
    
    generated_text = completion.choices[0].message.content  
    return generated_text
                
                
def display_main_app():
    st.title('AI Message Generator')
    selected_model = "gpt-4o"
    lang_option = st.selectbox(
    "Application language:",
    ("de", "en"))
    company_name = st.text_input("Enter your company name:")
    company_desc = st.text_area("Enter your company description:", height=50)
    job = st.text_area("Enter the job description:", height=50)
    person = st.text_input("Enter your name:")   
    
    mandatory_tags = st.multiselect("Select the tags you want to be in the message template:", options=["[fullName]", "[firstName]", "[lastName]", "[location]", "[jobTitle]", "[company]", "[emails]"])

    format = "linkedin-message"
    maxMessageLengthInCharacters = 2500
    
    if 'generated_message' not in st.session_state:
        st.session_state.generated_message = None

    if st.button('Generate Message'):

        if company_name and company_desc and job and person and len(mandatory_tags) > 0:
            formatted_prompt = system_instruction.format(
                PERSON_NAME=person,
                COMPANY_NAME=company_name,
                COMPANY_DESCRIPTION=company_desc,
                JOB_DESCRIPTION=job,
                MAX_MESSAGE_LENGTH=maxMessageLengthInCharacters,
                FORMAT=format,
                LANG_OPTION=lang_option
            )
            with st.spinner('Generating text... Please wait'):
                gpt_output = data_extraction(formatted_prompt, mandatory_tags)
                # Store the generated message in session state
                st.session_state.generated_message = gpt_output
                st.write(st.session_state.generated_message)
        else:
            st.error("Please fill in all the fields.")

    # If a message has been generated, show refinement options
    if st.session_state.generated_message:
        refinement = st.selectbox("Select a refinement:", list(REFINEMENTS.keys()))

        if st.button('Refine Message'):
            with st.spinner('Generating refined text... Please wait'):
                refined_prompt = refinement_prompt.format(
                    MESSAGE=st.session_state.generated_message,
                    REFINEMENT=refinement,
                    REFINEMENT_DESC=REFINEMENTS[refinement]
                )
                completion = client.chat.completions.create(
                    model=selected_model,
                    temperature=0.01,
                    messages=[{"role": "system", "content": refined_prompt}]
                )
                refined_output = completion.choices[0].message.content
                # Update the session state with the refined message
                st.title("Previous message:")
                st.write(st.session_state.generated_message)
                st.divider()
                st.title("Refined message:")
                st.write(refined_output)
                st.session_state.generated_message = refined_output
                
                
 
if not st.session_state.logged_in:
    display_login_form()
else:
    display_main_app()