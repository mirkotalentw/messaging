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

CRITICAL INSTRUCTIONS FOR MESSAGE GENERATION:

1. MANDATORY TAG USAGE:
   - You MUST use ALL tags selected by the user. This is non-negotiable.
   - Available tags: [fullName], [firstName], [lastName], [location], [jobTitle], [company], [emails]
   - If a tag is selected, it MUST appear in the message.

2. TAG CONTEXT:
   - ALL tags refer to the CANDIDATE, NOT the recruiter/sender.
   - [company] is the candidate's current company, NOT the recruiter's company.
   - [emails] are the candidate's email addresses, NOT the recruiter's.

3. GREETING RULES:
   - Start with "Hi", "Hello", or "Dear".
   - Use [firstName], [lastName], or [fullName] in greeting IF provided.
   - NEVER use [jobTitle], [company], or [location] in the greeting.
   - If no name tags are provided, use only "Hi", "Hello", or "Dear".

4. CANDIDATE-CENTRIC LANGUAGE:
   - ALL information in the message relates to the CANDIDATE.
   - NEVER use phrases like "At [company], we value..." or "Join our team at [company]".
   - AVOID any reference to the recruiter's company or location.

5. PROHIBITED CONSTRUCTIONS:
   - "Hello [jobTitle]" (INVALID)
   - "Dear [company] Candidate" (INVALID)
   - "Hello [location] professional" (INVALID)
   - Any sentence starting with a tag other than [firstName], [lastName], or [fullName]

6. CORRECT TAG USAGE EXAMPLES:
   - CORRECT: "I noticed you work at [company] as a [jobTitle]."
   - INCORRECT: "Join our team at [company]." ([company] is candidate's company, not recruiter's)
   - CORRECT: "Your experience in [location] is impressive."
   - INCORRECT: "I'll reach out to you at [emails]." ([emails] are candidate's, not recruiter's)
   
7. IMPORTANT TAG MEANING:
   - [fullName] is the full name of the candidate
   - [firstName] is the first name of the candidate
   - [lastName] is the last name of the candidate
   - [location] is the location of the candidate
   - [jobTitle] is the job title of the candidate
   - [company] is the company of the candidate
   - [emails] are the emails of the candidate
   
8. GENERAL INSTRUCTIONS:
    - If the user selects [fullName], [firstName], or [lastName], you MUST use all of them in the message. IN THIS CASE, YOU MUST FIND THE WAY AND USE ALL OF THEM IN THE MESSAGE. THIS IS MANDATORY. Only if they are provided of course.
    - Message cannot be shorter than 450 characters.
    - Try to use all data about writer/recruiter that is provided above: name, company, etc.
    
    
FAILURE TO FOLLOW THESE RULES WILL RESULT IN AN INVALID OUTPUT.
DOUBLE-CHECK YOUR MESSAGE BEFORE FINALIZING TO ENSURE ALL RULES ARE FOLLOWED.
"""

refinement_prompt = """
You are an HR assistant. Your task is to help with writing a message.
Here is the message:
{MESSAGE}
Please refine the message to make it more {REFINEMENT} - {REFINEMENT_DESC}.

The output MUST be only the message that the HR manager will send to the candidate. 
NO SUBJECT OR ANY OTHER TEXT SHOULD BE INCLUDED.

Use only tags that are in the original message template that user selected.

IMPORTANT INSTRUCTIONS FOR MESSAGE GENERATION:

The only tags that are allowed in the message are the ones that user selected in the original message template.

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