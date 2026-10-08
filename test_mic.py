import speech_recognition as sr

r = sr.Recognizer()

# Test each microphone
for i in [0, 1, 5, 9, 10]:
    print(f"\nTesting microphone index {i}...")
    try:
        with sr.Microphone(device_index=i) as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            print(f"Index {i} works! Speak something...")
            audio = r.listen(source, timeout=4, phrase_time_limit=8)
            text = r.recognize_google(audio)
            print(f"✅ Index {i} heard: {text}")
            break
    except sr.WaitTimeoutError:
        print(f"Index {i} - no speech detected")
    except sr.UnknownValueError:
        print(f"Index {i} - heard audio but could not understand")
    except Exception as e:
        print(f"Index {i} - error: {str(e)}")