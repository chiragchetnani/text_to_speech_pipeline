def run_groq(prompt , groq_client) :

    print(f'----|LOG : SENDING PROMPT : {prompt}')

    chat_completion = groq_client.chat.completions.create(
        messages = [
            {
                'role' : 'user' ,
                'content' : prompt
            }
        ] , model = 'llama3-70b-8192')

    return chat_completion.choices[0].message.content