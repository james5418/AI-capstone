from tkinter import *

class gameUI() :
    def __init__(self,replay,initMapStat, initGameStat,result,score) :
        self.replay = replay
        self.replay_index = 0

        self.window = Tk()
        self.window.title("battle sheep")
        self.window.geometry("660x470")
        self.window.resizable(0,0)
        self.canvas=Canvas(self.window , bg="#EEE8AC" , width=470, height=470)
        
        #12x12 fields
        self.dia = 36
        self.c_x = 10
        self.c_y = 36
        self.label = [ [None] * 12 for i in range(12) ]
        for i in range(0,12):
            for j in range(0,12):    
                t_label = Label(self.window,text='')
                if j%2 ==0:
                    t_label.place(x = self.c_x+i*self.dia +8, y = self.c_y+j*(self.dia-4) +8)                                      
                else:
                    t_label.place(x = self.c_x+i*self.dia+self.dia/2 +8, y = self.c_y+j*(self.dia-4) +8)
                self.label[i][j] = t_label
        

        self.text = Message(self.window,text='(initial state)',width=160)
        self.text.place(x=475,y=60)

        self.btn_next = Button(self.window, text='next', command=self.show_next)
        self.btn_next.place(x=520,y=340)

        self.btn_back = Button(self.window, text='back', command=self.show_back)
        self.btn_back.place(x=480,y=340)
        self.btn_back["state"] = DISABLED

        self.show_map(0)

        '''score_1 = Message(self.window, text=f'Player 1 get {score[0]}' , width=160, fg='#930000')
        score_1.place(x=475, y=200)
        score_2 = Message(self.window, text=f'Player 2 get {score[1]}', width=160, fg='#930000')
        score_2.place(x=475, y=220)
        score_3 = Message(self.window, text=f'Player 3 get {score[2]}'  , width=160, fg='#930000')
        score_3.place(x=475, y=240)
        score_4 = Message(self.window, text=f'Player 4 get {score[3]}'  , width=160, fg='#930000')
        score_4.place(x=475, y=260)'''

        show_result = Message(self.window,text='Final Result:\n'+result,width=160,fg='#930000')
        show_result.place(x=475,y=370)

        P1_label = Label(self.window,text='Player 1',bg="#FFB5B5")
        P1_label.place(x=480,y=10)
        P1_2abel = Label(self.window,text='Player 2',bg="#CEFFCE")
        P1_2abel.place(x=540,y=10)
        P1_3abel = Label(self.window,text='Player 3',bg="#FFF4C1")
        P1_3abel.place(x=480,y=35)
        P1_4abel = Label(self.window,text='Player 4',bg="#C4E1FF")
        P1_4abel.place(x=540,y=35)


        self.canvas.grid(row = 0 , column = 0)
        

    def show_next(self):
        self.replay_index = self.replay_index + 1

        self.text['text'] = self.replay[self.replay_index]['text']
        self.show_map(self.replay_index)
        
        
        if self.replay_index == len(self.replay)-1:
            self.btn_next["state"] = DISABLED
            self.text['text'] = self.text['text'] +'\n\nEND GAME'
        
        if self.replay_index >= 1:
            self.btn_back["state"] = NORMAL

    def show_back(self):
        self.replay_index = self.replay_index - 1

        self.text['text'] = self.replay[self.replay_index]['text']
        self.show_map(self.replay_index)

        
        if self.replay_index == 0:
            self.btn_back["state"] = DISABLED
        
        if self.replay_index < len(self.replay)-1:
            self.btn_next["state"] = NORMAL
            

    def show_map(self,i):
        action = self.replay[i]

        for i in range(0,12):
            for j in range(0,12):
                num = int(action['game'][i][j])

                if action['map'][i][j] == 1:
                    self.place_sheep([i,j],"#FFB5B5",num)
                elif action['map'][i][j] == 2:
                    self.place_sheep([i,j],"#CEFFCE",num)
                elif action['map'][i][j] == 3:
                    self.place_sheep([i,j],"#FFF4C1",num)
                elif action['map'][i][j] == 4:
                    self.place_sheep([i,j],"#C4E1FF",num)
                elif action['map'][i][j] == -1:
                    self.paint_circle([i,j],"gray")
                else:
                    self.paint_circle([i,j],"white")
                

    def paint_circle(self,pos,color):
        i = pos[0]
        j = pos[1]

        self.label[i][j]['bg']=color
        self.label[i][j]['text']=''

        if j%2 ==0:
            self.canvas.create_oval(self.c_x+i*self.dia, self.c_y+j*(self.dia-4),
                                           self.c_x+(i+1)*self.dia, self.c_y+j*(self.dia-4)+self.dia, fill=color)
        else:
            self.canvas.create_oval(self.c_x+i*self.dia+self.dia/2, self.c_y+j*(self.dia-4),
                                            self.c_x+(i+1)*self.dia+self.dia/2, self.c_y+j*(self.dia-4)+self.dia, fill=color)

    def place_sheep(self,pos,color,num):
        i = pos[0]
        j = pos[1]

        self.paint_circle(pos,color)
        self.label[i][j]['text'] = str(num)



