I am planning three great projects. Contents below:
1. It is a mock interview agent which will mimic a human interviewer and conduct an interview with a student and provide feedback. I'll build it from scratch.
Work Flow or journey
1. The user will input their resume, and a chat system will open.
2. After the resume is entered into the system, it will be parsed.
3. Once the resume is parsed, a chat system will behave as or simulate a human interviewer with the student taking an actual interview.


Use a local resume PDF from the ignored `private/inputs` directory as the reference input.


I have thought a lot about how the system should look, and I will explain the system below:
I want to build this system in multiple phases.
1. Phase 1: The interviewer asks the candidate "tell me about yourself" questions to gain a brief understanding of the candidate.
2. The interviewer has the resume, and after hearing from the candidate, they will form a basic understanding of what types of questions need to be asked next.

Phase 2 is where the real technical interview will get started. The interviewer will identify the best project completed by the candidate. For example, they might select the first project from the experience section, or they may navigate to the project section and ask what the most important project is that the candidate has done. the interviewer will follow a russian doll approach, starting from a high level and drilling down until the student is able to answer properly or is no longer able to answer. This is a very important step. You can think of it as the Socratic method, where you have to ask them what they have built and what the project is about and ask more questions based on the answers they give.

Based on their approach, you then have to drill down and ask more cross-questions according to the answers they have given. You have to keep drilling down again and again to go deep into the details. Remember the job is for Learning Engineer so when you drill down and ask questions to the student, it should be from the point of view of a Machine Learning Engineer and align with the job description, as the job description is also for a Machine Learning Engineer.
Let me give you an example of what I mean by "drill down."
If a person tells me that he has built a retrieval-augmented generation project, I will ask him what he built. "How does it work?" then, "What do you mean by RAG?"Then I will ask them, "What are the different chunking strategies you are following?"What are the trade-offs they have taken in their chunking strategies? Then I will ask them, "What is vector indexing?" and "Could you tell me the difference between HNSW and IVA Flat? then I'll ask them about cosine similarity and what the formula for cosine similarity. What is the advantage of RAG here, and why didn't he use fine-tuning here?
What are the disadvantages of RAG here? This is how I wanted to drill down into every single project.
1. How do you handle vector indexing for high-dimensional data?
2. What are the specific trade-offs between HNSW and IVF Flat in this architecture?
3. In terms of RAG, how are you measuring cosine similarity across different embedding models?
4. Are we prioritizing fine-tuning the base model or optimizing the retrieval pipeline first?
5. Smartly construct follow-up questions based on the answers provided. The goal is to understand their machine learning concepts by using their project as a proxy and going deep.


In Phase 3, I will ask them about different projects or research projects or any internship they have completed. We will also follow the "Russian Doll" questioning approach (or the Socratic method of questioning) here, as I mentioned in Phase 2.
One thing I wanted to mention: in Phase 2 and Phase 3, if the candidate is stuck somewhere, please provide a nudge or some hint to them so that they can proceed with the interview.

Now in Phase 4, we'll ask the factual questions about the machine learning concepts.
 Here are some things we should think about regarding the factual questions:
 https://github.com/andrewekhalel/MLQuestions

 I want to access the GitHub link and understand what the questions are. After understanding the questions, you should download all of them and put them in a markdown file. You can use a simple 384-dimensional embedding model.

 Based on the candidate, understand from which field they are coming. For example, they can come from computer vision, NLP, or any other field.Now that we have a list of which fields they are coming from, you have to go to the markdown file, perform a similarity search, and retrieve the questions related to the fields mentioned in that list. Ask those questions. If you do not find any questions from the markdown file that is created from the GitHub link, you can ask your questions on your own. And ask at least five questions from their field, or perhaps from a different field, related to their resume. These should be factual questions so that we can verify their answers and properly evaluate the student. At least ask four to five questions to give the grade properly.


 Now I will move into Phase 5.

In Phase 5, we will ask behavioral questions, such as:
1. Why do you want to do this job?
2. How do you work in a team?
3. Tell me about a situation where you had to convince your senior or your manager. For example, tell me about a time when your manager told you that you have to do a specific task, but you found that it was not the correct approach. How did you handle that situation?
4. How do you see yourself in five years?
5. Do you have any questions for me?


Now I want to evaluate the candidate based on the responses that are coming in each of the five phases.
Now I want to create robust evaluation criteria to evaluate the candidate in each of the five phases and create a single score.
Now, let me talk about the evaluation criteria of these phases for you.

In phase 1, it doesn't make sense to include the evals. This stage is more about letting candidates describe how they think and explain things about themselves.

In Phase 2, I want to use the Russian Doll  or the Socratic  as a metric. This involves a deep dive into each answer to see how they dig deeper and deeper until they reach the base level. The goal is to determine whether or not they are providing answers by following a first principles approach. basically, how deep they can go in each answer and how many layers they can dig into for a true deep dive.

Phase 3 is similar to Phase 2.
Also, since you have provided hints in Phase 2 and Phase 3, after providing each hint, you should also evaluate whether the candidate is moving toward the correct answer or not by using hint.


Phase 4 is the easier one to use because Phase 4 is more about factual questions. If you are asking four, five, or six questions, you have to understand out of those five questions how many they have given the correct answer for.


In Phase 5, you have to understand if the person is visionary and can think on a larger scale. You also need to determine:
1. Whether the person is a good team player
2. Whether they have a good vision and work for the cause to make people's lives better.
3. Grounded and realistic and empathy for the user and for the team player


4. Interaction Design
   (a) I don't want you to build a video feature right now. The interface should be an audio conversation between the student and the chatbot.
   (b) If the student is speaking too fast, they may be anxious or unable to handle the interview properly.
   (c) The chatbot must demonstrate empathy in these moments. For example, it could suggest: "Take a glass of water and pause for a moment. You can take a two-minute break; I am here and I am waiting for you." And continue. Then, after that, continue asking the chain of questions.

   In the initial version, I don't want the video feature, but maybe we can consider it for a later version. By analyzing the video of the student, we can better understand their answers or their tendencies during the interview.


Tone of the interviewer: I want the tone of the interviewer to be professional, not too enthusiastic and eager as LLM models often are. You have to be professional. Remember that you are an interviewer; you shouldn't show too much happy emotions and you shouldn't act to please the candidate. You should just act naturally as an interviewer conducting an interview: empathetic, but not too eager or emotional about whether they are correct or performing well. The words and sentences you use should be concise, to the point, and in simple English. Add to the prompt template to never use phrases like "good answer," "perfect answer," or "impressive" or 'let's move to the next'. When the candidate gives an answer, do not have the AI simply agree with the person who is prompting. In a real interview, the interviewer understands the answer and, based on that response, asks follow-up questions.

You have to understand the answer and ask follow-up questions until:
1. The whole concept is clear.
2. The interviewer finds that the person truly knows the material and the concept is clear to them.


Features:
1. A large language model which will power this entire application. 2. I wanted to use GPT's reasoning model.the reasoning model gpt-5.4
Here is an example of how you should work with GPT-5.4.


from openai import OpenAI

client = OpenAI()

prompt = """
Write a bash script that takes a matrix represented as a string with
format '[1,2],[3,4],[5,6]' and prints the transpose in the same format.
"""

response = client.responses.create(
    model="gpt-5.4",
    reasoning={"effort": "low"},
    input=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print(response.output_text)




Now for the voice part, let us do something interesting.
We will use OpenAI's whispr model, which is a text to speech model. which is the best.
You can ask me for my OpenAI API key. I will provide it to you, but please never expose this API key to anyone.
When we are on GitHub, we should store it in .gitignore.

One thing I wanted to tell you: when the user uploads the PDF, please pass the PDF via OpenAI API, but maybe don't use any python like pynum.pdf library, because it is not reliable.
On the resume, please parse the resume PDF, convert into the different sections, and store them in a database.

Database: Supabase
Let's use Supabase as a database.

I will give you the access key for Supabase. You have to use the access key to store the relevant section in Supabase project and database tables.

I want you to create a score for each of the four phases, as well as a final combined score calculated from all of them.
I also want to develop an anti-cheating system, but not right now. Maybe we will do it future.
I also wanted to build a full CI/CD pipeline which pushes to GitHub and links it to AWS, but not right now. Maybe we can build it in a coming version in the future or in subsequent versions

These are the subsequent versions:

1. CI/CD pipeline
   (a) Connect to GitHub
   (b) Link to AWS
   This is the first thing we will build in subsequent versions.

2. Anti-cheating features
   (a) Block users based on face recognition
   (b) Other blocking mechanisms
   If a person is cheating, we want to block them using facial recognition or other methods we create. This will be included in the subsequent versions.


   I don't want you to build this project right away. First, create a PRD (Product Requirement Document). provide a timeline of the things we will build. And create a list of tasks which you will finish.

   Once I approve the PRD and the project, you can follow the document to finish the tasks one by one and mark them as done.
   I think I have PRD and dev skills you can invoke while building this. If I don't have these skills, go ahead and start building.

   Runtime credentials are stored outside version-controlled project files.

   Do not expost it anywhere. Tell me if you need anyother creds.
