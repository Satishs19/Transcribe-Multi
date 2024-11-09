from django.http import HttpResponse,JsonResponse
from django.template import loader
from django.shortcuts import render
import speech_recognition as sr
from django.views.decorators.csrf import csrf_exempt
import os
from django.conf import settings
import ollama
from pydub import AudioSegment

def index(request):
  template = loader.get_template('transcribe.html')
  return HttpResponse(template.render())

@csrf_exempt
def recognize_speech(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        temp_dir = "transcribe/temp_audio"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, audio_file.name)

        # Saving the audio file
        with open(temp_file_path, 'wb+') as temp_file:
            for chunk in audio_file.chunks():
                temp_file.write(chunk)

        # Convert the audio file to WAV format
        audio = AudioSegment.from_file(temp_file_path)
        wav_file_path = os.path.join(temp_dir, 'converted_audio.wav')
        audio.export(wav_file_path, format='wav')

        recognizer = sr.Recognizer()
        try:
            with sr.AudioFile(wav_file_path) as source:
                audio = recognizer.record(source)
                text = recognizer.recognize_google(audio, language="hi-IN")
        except sr.UnknownValueError:
            return JsonResponse({'error': 'Sorry, I could not understand the audio.'})
        except sr.RequestError as e:
            return JsonResponse({'error': f'Could not request results; {e}'})
        finally:
            # Ensure the temp files are deleted after processing
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if os.path.exists(wav_file_path):
                os.remove(wav_file_path)
        print(text)
        # return JsonResponse({'text': text})
        client=ollama.Client()
        prompt = f"""
        You are an AI language model designed to correct grammatical errors and spelling mistakes in Hindi text. Your task is to make corrections without adding any additional information that is not present in the original text. Additionally, if you encounter the words "next line" or "अगली लाइन" or "नेक्स्ट लाइन", you should start a new line and continue the remaining text on the new line. Here is an example of how you should perform the corrections:
        Original Text: "मुझे कल बाजार जाना है और कुछ सब्जियां खरीदन है"
        Corrected Text: "मुझे कल बाजार जाना है और कुछ सब्जियां खरीदनी हैं।"

        Original Text: "वह बहुत अच्छा गाता है और सबको पसंद आता है।"
        Corrected Text: "वह बहुत अच्छा गाता है और सबको पसंद आता है।"

        Original Text: "मुझे कल बाजार जाना है। अगली लाइन मुझे कुछ सब्जियां खरीदनी हैं।"
        Corrected Text: "मुझे कल बाजार जाना है।\nमुझे कुछ सब्जियां खरीदनी हैं।"

        Original Text: "वह बहुत अच्छा गाता है। next line सबको पसंद आता है।"
        Corrected Text: "वह बहुत अच्छा गाता है।\nसबको पसंद आता है।"

        Original Text: "आपका नाम क्या है नेक्स्ट लाइन आपके पिताजी का नाम क्या है"
        Corrected Text: "आपका नाम क्या है?\nआपके पिताजी का नाम क्या है?"

        Original Text: "आपका नाम क्या है"
        Corrected Text: "आपका नाम क्या है?"

        Please correct the following text:
        {text}
        """
        response = client.generate(prompt=prompt, model="llama3.1")
        formatted_text = response['response']
        print(formatted_text)
        return JsonResponse({'text': formatted_text})
    return render(request, 'transcribe.html')