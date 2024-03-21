from tkinter import *
from tkinter import filedialog
import tkinter as tk
from PIL import Image,ImageTk
import cv2
import os
import math
import shutil
import webbrowser
from subprocess import call,STDOUT
from stegano import lsb #pip install stegano
import wave
from cryptography.fernet import Fernet
from tkinter import messagebox



root=Tk()
root.title("SteganoSynch -Hide your secreter information into another Media")
root.geometry("700x550+150+180")
root.resizable(False,False)
root.configure(bg="#FF6103") 

key = Fernet.generate_key()
cipher = Fernet(key)

def showImage():
    global filename
    filename=filedialog.askopenfilename(initialdir=os.getcwd(),
                                        title='Select Image File',
                                        filetypes=(("PNG file",".png"),
                                                   ("JPG file",".jpg"),("JPEG file",".jpeg"),("MP4 file", "*.mp4"),("MOV file", "*.mov"),("WAV file","*.wav"),("All file","*.*")))
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        openImage(filename)
    elif filename.lower().endswith('.mp4'):
        openVideo()
    elif filename.lower().endswith('.mov'):
        openVideo()
    elif filename.lower().endswith('.wav'):
        open_audio(filename)
    elif filename=="secrete.wav":
        open_audio(filename)




def openImage(filename):
    img = Image.open(filename)
    img = ImageTk.PhotoImage(img)
    lbl.configure(image=img, width=280, height=280)
    lbl.image = img

def openVideo():
    global filename
    cap = cv2.VideoCapture(filename)
    
    
    def show_frame():
        nonlocal cap
        ret, frame = cap.read()
        if ret:
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized_frame = cv2.resize(frame, (340, 280))
            resized_frame = Image.fromarray(resized_frame)
            resized_frame = ImageTk.PhotoImage(resized_frame)
            lbl.configure(image=resized_frame)
            lbl.image = resized_frame
            
            lbl.after(10, show_frame)
        else:
            cap.release()

    show_frame()

def open_audio(filename):
    try:
        audio = wave.open(filename, "rb")
        frames = audio.readframes(audio.getnframes())
        audio.close()
        return frames
    except Exception as e:
        print("Error:", e)
        return None

def split_string(s_str,count=10):
    per_c=math.ceil(len(s_str)/count)
    c_cout=0
    out_str=''
    split_list=[]
    for s in s_str:
        out_str+=s
        c_cout+=1
        if c_cout == per_c:
            split_list.append(out_str)
            out_str=''
            c_cout=0
    if c_cout!=0:
        split_list.append(out_str)
    return split_list




def frame_extraction(video):
    if not os.path.exists("./tmp"):
        os.makedirs("tmp")
    temp_folder="./tmp"
    print("[INFO] tmp directory is created")

    vidcap = cv2.VideoCapture(video)
    count = 0

    while True:
        success, image = vidcap.read()
        if not success:
            break
        cv2.imwrite(os.path.join(temp_folder, "{:d}.png".format(count)), image)
        count += 1 

def encode_string(input_string,root="./tmp/"):
    split_string_list=split_string(input_string)
    for i in range(0,len(split_string_list)):
        f_name="{}{}.png".format(root,i)
        if os.path.isfile(f_name):
            secret_enc = lsb.hide(f_name, split_string_list[i])
            secret_enc.save(f_name)
            print("[INFO] frame {} holds {}".format(f_name, split_string_list[i]))
        else:
            print("[ERROR] Frame {} not found.".format(f_name))  

def clean_tmp(path="./tmp"):
    if os.path.exists(path):
        shutil.rmtree(path)
        print("[INFO] tmp files are cleaned up")
    
def Hide():
    global filename
    global secrete
    message=input_string.get(1.0,END)
    
    if not message:
        print("Please provide a message to hide")
        return 
    if not filename:
        print("please select a media file")
        return 
    
    secret_key = entry_secret_key.get()
    n=len(secret_key)
    if n<5 and n>0:
           messagebox.showinfo("Error", "Length of the secrete key should be 5!")
           return
    if not secret_key:
        messagebox.showinfo("Error", "Please provide a secret key")
        return
    secret_key_bytes = bytes(secret_key, 'utf-8')
    encrypted_message = cipher.encrypt(bytes(message, 'utf-8')).decode('utf-8')
    
    if filename.lower().endswith('.mp4'):
        frame_extraction(filename)
        final_message=secret_key+message
        call(["ffmpeg", "-i",filename, "-q:a", "0", "-map", "a", "tmp/audio.mp3", "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)
    
        encode_string(final_message)
        call(["ffmpeg", "-i", "tmp/%d.png" , "-vcodec", "png", "tmp/video.mov", "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)
    
        call(["ffmpeg", "-i", "tmp/video.mov", "-i", "tmp/audio.mp3", "-codec", "copy", "video.mov", "-y"],stdout=open(os.devnull, "w"), stderr=STDOUT)
        clean_tmp()

    elif filename.lower().endswith('.wav'):
        nameoffile=filename
        song = wave.open(nameoffile, mode='rb')

        nframes=song.getnframes()
        frames=song.readframes(nframes)
        frame_list=list(frames)
        frame_bytes=bytearray(frame_list)

        data = secret_key+message

        res = ''.join(format(i, '08b') for i in bytearray(data, encoding ='utf-8'))     
        print("\nThe string after binary conversion :- " + (res))   
        length = len(res)
        print("\nLength of binary after conversion :- ",length)

        data = data + '*^*^*'

        result = []
        for c in data:
            bits = bin(ord(c))[2:].zfill(8)
            result.extend([int(b) for b in bits])

        j = 0
        for i in range(0,len(result),1): 
            res = bin(frame_bytes[j])[2:].zfill(8)
            if res[len(res)-4]== result[i]:
               frame_bytes[j] = (frame_bytes[j] & 253)      #253: 11111101
            else:
               frame_bytes[j] = (frame_bytes[j] & 253) | 2
               frame_bytes[j] = (frame_bytes[j] & 254) | result[i]
            j = j + 1
    
        frame_modified = bytes(frame_bytes)

        stegofile="secrete.wav"
        with wave.open(stegofile, 'wb') as fd:
             fd.setparams(song.getparams())
             fd.writeframes(frame_modified)
        print("\nEncoded the data successfully in the audio file.")    
        song.close()
    else:
       final_message=secret_key+message
       secrete=lsb.hide(str(filename),final_message)

def Show():
    global filename,key,cipher
    if filename.lower().endswith('.mov'):
        frame_extraction(filename)
        secret = []
        root = "./tmp/"
        n=len(os.listdir(root))
        for i in range(n):
           f_name = "{}{}.png".format(root, i)
           try:
              secret_dec = lsb.reveal(f_name)
              secret.append(secret_dec)
           except IndexError as e:
               print("Message hidden till this file", f_name)
               break  
        clear_message=''.join(secret)
        secret_key = entry_secret_key.get()
        key3=secret_key
        if not secret_key:
           messagebox.showinfo("Error", "Please provide a secret key")
           return
       #secret_key_bytes = bytes(secret_key, 'utf-8')
        try:
            decrypted_message = cipher.decrypt(bytes(clear_message, 'utf-8')).decode('utf-8')
        except Exception:
            # If decryption fails, assume the message is not encrypted
            decrypted_message = clear_message
       
        n=len(key3) 
        if key3 not in decrypted_message or n<5:
            messagebox.showinfo("Error", "wrong secrete key!!")
        else:
            input_string.insert(END,decrypted_message[5:])

        clean_tmp()   
    elif filename.lower().endswith('.wav'):
        nameoffile=filename
        song = wave.open(nameoffile, mode='rb')

        nframes=song.getnframes()
        frames=song.readframes(nframes)
        frame_list=list(frames)
        frame_bytes=bytearray(frame_list)

        extracted = ""
        p=0
        for i in range(len(frame_bytes)):
            if(p==1):
               break
            res = bin(frame_bytes[i])[2:].zfill(8)
            if res[len(res)-2]==0:
               extracted+=res[len(res)-4]
            else:
               extracted+=res[len(res)-1]
    
            all_bytes = [ extracted[i: i+8] for i in range(0, len(extracted), 8) ]
            decoded_data = ""
            for byte in all_bytes:
                decoded_data += chr(int(byte, 2))
                if decoded_data[-5:] == "*^*^*": 
                   clear_message= ''.join(decoded_data[:-5]) 
                   secret_key = entry_secret_key.get()
                   key2=secret_key
                   if not secret_key:
                      messagebox.showinfo("Error", "Please provide a secret key")
                      return
                   #secret_key_bytes = bytes(secret_key, 'utf-8')

                   try:
                       decrypted_message = cipher.decrypt(bytes(clear_message, 'utf-8')).decode('utf-8')
                   except Exception:
                   # If decryption fails, assume the message is not encrypted
                       decrypted_message = clear_message
                   n=len(key2) 
                   if key2 not in decrypted_message or n<5:
                      messagebox.showinfo("Error", "wrong secrete key!!") 
                   else:                       
                      input_string.insert(END,decrypted_message[5:])
                   
                   #print("The Encoded data was :--",decoded_data[:-5])
                   p=1
                   break  


    else:
       clear_message=lsb.reveal(filename)
       
       secret_key = entry_secret_key.get()
       n=len(secret_key)           
       key1=secret_key
       if not secret_key:
           messagebox.showinfo("Error", "Please provide a secret key")
           return
       #secret_key_bytes = bytes(secret_key, 'utf-8'
       try:
            decrypted_message = cipher.decrypt(bytes(clear_message, 'utf-8')).decode('utf-8')
       except Exception:
            # If decryption fails, assume the message is not encrypted
            decrypted_message = clear_message
       
       input_string.delete(1.0,END)
       if key1 not in decrypted_message or n<5:
           messagebox.showinfo("Error", "wrong secrete key!!")
       else:   
           input_string.insert(END,decrypted_message[5:])

def Save():
    secrete.save("Hidden.png")


#icon

entry_secret_key = Entry(root, show="*", font="robote 20", bg="white", fg="black", relief=GROOVE)
entry_secret_key.place(x=310, y=485, width=360, height=40)
Label(root,text="Enter Secrete Key Here:",bg="#FF6103",fg="black",font="Georgia 14 bold underline").place(x=30,y=495)

#Head
Label(root,text="StyganoSynch",bg="#FF6103",fg="white",font="Georgia 25 bold underline").place(x=200,y=20)

#first Frame
f=Frame(root,bd=3,bg="black",width=340,height=280,relief=GROOVE)
f.place(x=10,y=80)

lbl=Label(f,bg="black")
lbl.place(x=40,y=10)

#second Frame
frame2=Frame(root,bd=3,width=340,height=280,bg="white",relief=GROOVE)
frame2.place(x=350,y=80)

input_string=Text(frame2,font="robote 20",bg="white",fg="black",relief=GROOVE,wrap=WORD)
input_string.place(x=0,y=0,width=320,height=295)

scrollbar1=Scrollbar(frame2)
scrollbar1.place(x=320,y=0,height=300)

scrollbar1.configure(command=input_string.yview)
input_string.configure(yscrollcommand=scrollbar1.set)

#third Frame
frame3=Frame(root,bd=3,bg="#FF9912",width=680,height=100,relief=GROOVE)
frame3.place(x=10,y=370)

Button(frame3,text="Open Media",width=10,height=3,font="Georgia 10 bold",command=showImage).place(x=20,y=20)
Button(frame3,text="Save Media",width=10,height=3,font="Georgia 10 bold",command=Save).place(x=150,y=20)
Button(frame3,text="Hide Data",width=10,height=3,font="Georgia 10 bold",command=Hide).place(x=280,y=20)
Button(frame3,text="Show Data",width=10,height=3,font="Georgia 10 bold",command=Show).place(x=415,y=20)
Button(frame3,text="Share Media",width=10,height=3,font="Georgia 10 bold",command=lambda: webbrowser.open("https://mail.google.com/")).place(x=550,y=20)
#Label(frame3,text="picture,Image,Photo File",bg="#FF9912",fg="black").place(x=20,y=5)


#fourth Frame
'''frame4=Frame(root,bd=3,bg="#FF9912",width=330,height=100,relief=GROOVE)
frame4.place(x=360,y=370)

Button(frame4,text="Hide Data",width=10,height=2,font="Georgia 14 bold",command=Hide).place(x=20,y=20)
Button(frame4,text="Show Data",width=10,height=2,font="Georgia 14 bold",command=Show).place(x=180,y=20)
#Label(frame4,text="picture,Image,Photo File",bg="#FF9912",fg="black").place(x=20,y=5)'''




root.mainloop()
