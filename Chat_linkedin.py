import streamlit as st
from openai import OpenAI
import os 
# You would need to import a library for your chosen scraping service here, e.g.,
# import your_scraping_service

# Title of the app
st.title("LinkedIn to HR Questionnaire Generator")

# Check if the API key is available in secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("OpenAI API key not found in Streamlit secrets. Please add it to your .streamlit/secrets.toml file.")
else:
    # Load the API key from Streamlit secrets
    api_key = st.secrets["OPENAI_API_KEY"]
    
    # Create an OpenAI client instance with the API key
    client = OpenAI(api_key=api_key)

    # --- Step 1: Replace dummy data with a real scraping function ---
    def scrape_linkedin_profile(url):
        """
        This is a placeholder for a real scraping service API call.
        In a real application, you would use a paid service like Phantombuster
        or Apify to get structured data from a LinkedIn URL.
        """
        # For demonstration purposes, we return a hardcoded dictionary.
        # This is where your actual API call would go.
        # For example: 
        # response = requests.get(f"https://api.scraper.com/v1/linkedin?url={url}&api_key=your_key")
        # return response.json()
        
        return {
            "name": "Alex Johnson",
            "current_role": "Data Scientist",
            "current_company": "TechFusion Solutions",
            "about": "A highly motivated data scientist with 5 years of experience in machine learning, data visualization, and predictive modeling. Passionate about leveraging data to solve complex business problems. Experience working with Python, SQL, and cloud platforms like AWS and Google Cloud.",
            "experience": [
                {
                    "role": "Data Scientist",
                    "company": "TechFusion Solutions",
                    "duration": "2021 - Present",
                    "description": "Developed and deployed machine learning models to improve customer engagement and reduce churn. Led a project to build a real-time analytics dashboard using Python and Tableau."
                },
                {
                    "role": "Data Analyst",
                    "company": "Data Insights Co.",
                    "duration": "2018 - 2021",
                    "description": "Analyzed large datasets to provide actionable insights for marketing campaigns. Created weekly reports for senior management on key performance indicators."
                }
            ],
            "skills": ["Python", "Machine Learning", "SQL", "Tableau", "AWS", "Statistical Analysis"]
        }

    # User input for the LinkedIn URL
    linkedin_url = st.text_input("Enter LinkedIn Profile URL:")

    if st.button("Generate Questions"):
        if not linkedin_url:
            st.warning("Please enter a LinkedIn URL.")
        else:
            with st.spinner("Scraping and analyzing profile..."):
                try:
                    # Call the scraping function to get the real data
                    scraped_data = scrape_linkedin_profile(linkedin_url)

                    # Extract company name and 'About' section for the prompt
                    company_name = scraped_data.get("current_company", "a candidate's current company")
                    about_section = scraped_data.get("about", "No 'About' section provided.")
                    
                    # Step 2: Construct the prompt for OpenAI
                    experience_str = '\n'.join([
                        f"Role: {exp['role']}, Company: {exp['company']}, Description: {exp['description']}"
                        for exp in scraped_data.get("experience", [])
                    ])
                    
                    prompt = f"""
                    You are an HR assistant. Your task is to generate interview questions for a candidate based on their LinkedIn profile.
                    
                    Here is the candidate's information:
                    Name: {scraped_data.get("name")}
                    Current Role: {scraped_data.get("current_role")}
                    Current Company: {company_name}
                    
                    About the candidate: {about_section}
                    
                    Experience:
                    {experience_str}
                    
                    Skills: {', '.join(scraped_data.get("skills", []))}
                    
                    Based on this information, please prepare 5-7 open-ended questions that an HR professional can use to assess this candidate. The questions should be tailored to their experience and role.
                    """
        
                    # Step 3: Call the OpenAI API using the client instance
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a helpful HR assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    # Step 4: Display the generated questions
                    questions = response.choices[0].message.content
                    st.subheader(f"Interview Questions for {scraped_data.get('name')}")
                    st.write(f"**Company:** {company_name}")
                    st.write(f"**Role:** {scraped_data.get('current_role')}")
                    st.markdown(questions)
                
                except openai.AuthenticationError:
                    st.error("Invalid API key. Please check your key in the secrets.toml file.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")
