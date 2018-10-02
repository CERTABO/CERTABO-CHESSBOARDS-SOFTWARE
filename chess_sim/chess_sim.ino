#include "SoftwareSerial.h"
int pot_pin = A0;    // select the input pin for the potentiometer
int a = 120; // empty board
int button_pin = 10;

SoftwareSerial mySerial(8, 9); // RX, TX

long t,T_send;
char start_board[]={"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"};
char error2_board[]={"rnbqkbnr/2ppp2p/1p4p1/6N1/4P3/p1N2Q2/PPPP1PPP/R1B1K2R"};
char current_board[100];

void show_board() {
  int i,j,line,len = strlen( current_board ); 
  char c;
  mySerial.println("**** Board state ****"); 

  mySerial.println("---a b c d e f g h"); 
  line=8;
  mySerial.print("8 |");
  for(i=0;i<len;i++) {
    c = current_board[i];
    if ((c>=0x30)and(c<=0x39)) {
      for(j=0;j<(c-0x30);j++) mySerial.print(" |");
    }
    else if (c=='/') {mySerial.println(); line--; mySerial.print(line); mySerial.print(" |"); }
    else { mySerial.print((char)c); mySerial.print("|"); }
  }
  mySerial.println(); 
  mySerial.println("---a b c d e f g h"); 
    
}

void reset_board() {
  int len = strlen( start_board ),i;
  for(i=0;i<len;i++) current_board[i] = start_board[i];
  current_board[i]=0;
}

void set_error2_board() {
  int len = strlen( error2_board ),i;
  for(i=0;i<len;i++) current_board[i] = error2_board[i];
  current_board[i]=0;
}


void setup() {
  pinMode(button_pin, INPUT_PULLUP);
  Serial.begin(38400); 
  mySerial.begin(9600);
  mySerial.println( "\n\n\n\n(C)2018 NKB RUS Bluetooth chess simulator\n\n" );
  mySerial.println( "******************************************" );
  mySerial.println( "r - reset board to start position," );
  mySerial.println( "s - show current board state," );
  mySerial.println( "t - get time," );
  mySerial.println( "e2e4 - move piece (any move, like d3d5...)" );
  mySerial.println( "z - set position as eerror2.sav," );
  mySerial.println( "******************************************" );
  mySerial.println( "Now type your command:" );
  
  
  reset_board();
  T_send = millis()+1000u;
}

//White only:

// rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

char empty[] = {"0 0 0 0 0"};
char empty2[] = {"0 0 56 0 0"};
char empty3[] = {"201 0 0 0 0"};

char rook[] = {"101 2 3 4 5"};
char knight[] = {"201 2 32 4 57"};
char bishop[] = {"202 27 32 4 57"};
char queen[] = {"202 27 32 41 57"};
char king[] = {"208 0 345 1 84"};
char rook2[] = {"101 26 3 4 5"};
char knight2[] = {"201 26 32 41 57"};
char bishop2[] = {"202 276 32 4 57"};
char pawn1[] = {"211 0 132 63 192"};
char pawn2[] = {"210 0 122 200 59"};
char pawn3[] = {"210 0 120 18 31"};
char pawn4[] = {"210 0 122 211 16"};
char pawn5[] = {"203 0 115 113 114"};
char pawn6[] = {"203 0 116 73 95"};
char pawn7[] = {"203 0 116 173 95"};
char pawn8[] = {"203 0 116 273 95"};


char Rook[] = {"3 0 115 87 237"};
char Knight[] = {"3 0 115 41 35"};
char Bishop[] = {"3 0 116 59 170"};
char King[] = {"3 0 116 84 26"};
char Queen[] = {"3 0 116 74 26"};
char Bishop2[] = {"3 0 116 59 17"};
char Knight2[] = {"3 0 115 45 192"};
char Rook2[] = {"11 0 132 10 164"};
char Pawn1[] = {"11 0 132 63 192"};
char Pawn2[] = {"10 0 122 200 59"};
char Pawn3[] = {"10 0 120 18 31"};
char Pawn4[] = {"10 0 122 211 16"};
char Pawn5[] = {"3 0 115 113 114"};
char Pawn6[] = {"3 0 116 73 95"};
char Pawn7[] = {"3 0 116 173 95"};
char Pawn8[] = {"3 0 116 273 95"};


//const char real_board[] PROGMEM = 
//{":0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 0 116 73 95 3 0 115 113 114 10 0 122 211 16 10 0 120 18 31 0 0 0 0 0 10 0 122 200 59 11 0 132 63 192 11 0 132 10 164 3 0 116 59 73 3 0 115 45 192 3 0 116 59 17 3 0 116 74 26 0 0 0 0 0 0 0 0 0 0 3 0 115 41 35 3 0 115 87 237"};
//const char start_board[] PROGMEM = 
//{":0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 3 0 116 73 95 3 0 115 113 114 10 0 122 211 16 10 0 120 18 31 0 0 0 0 0 10 0 122 200 59 11 0 132 63 192 11 0 132 10 164 3_ 0 116 59 73_ 3 0 115 45 192_ 3 0 116 59 17_ 3 0 116 74 26_ 0 0 0 0 0_ 0 0 0 0 0_ 3 0 115 41 35_ 3 0 115 87 237"};
//const char empty_board[] PROGMEM = 
//{":1 2 3 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 9"};


// i = counter of cells, n = number of empty cells to send
void print_empty(int i, int n) {
  if (i) Serial.print(' ');
  for( i=0; i<n; i++ ) {
    if (i) Serial.print(' ');
    if (random(100)>20)
      Serial.print(empty2);
    else if (random(100)>20)
      Serial.print(empty3);
    else Serial.print(empty);
  }
} 
 


void send_data( char *board ) {
  char c;
  int len = strlen( board ), j;
  // counters for pieces, because each piece have different code
  char p=0,r=0,n=0,b=0;
  char P=0,R=0,N=0,B=0;
  
  Serial.print(':');
  for(int i=0; i<len; i++) {
//    c = pgm_read_byte_near( board + i ); 
    c = board[i]; 
    
    if ((c>0x40)&&(i)) Serial.print(' '); // a piece, not empty or just slash
    
    switch (c) {

      case 'r':
        if (random(100)>20) {
          if (r==0) Serial.print(rook);
          else Serial.print(rook2);
          r++;
        }
        else
          Serial.print(rook2);
        break;
        
      case 'n':
        if (random(100)>20) {
          if (n==0) Serial.print(knight);
          else Serial.print(knight2);
          n++;
        }
        else
          Serial.print(knight);
        break;
        
      case 'b':
        if (b) Serial.print(bishop);
        else Serial.print(bishop2);
        b++;
        break;
        
      case 'q':
        Serial.print(queen);
        break;
        
      case 'k':
        Serial.print(king);
        break;
        
      case 'p':
        switch(p) {
          case 0: Serial.print(pawn1); break;
          case 1: Serial.print(pawn2); break;
          case 2: Serial.print(pawn3); break;
          case 3: Serial.print(pawn4); break;
          case 4: Serial.print(pawn5); break;
          case 5: Serial.print(pawn6); break;
          case 6: Serial.print(pawn7); break;
          case 7: Serial.print(pawn8); break;
        }
        p++;  
        break;
        
      case 'R':
        if (R) Serial.print(Rook);
        else Serial.print(Rook2);
        R++;
        break;
        
      case 'N':
        if (N) Serial.print(Knight);
        else Serial.print(Knight2);
        N++;
        break;
        
      case 'B':
        if (B) Serial.print(Bishop);
        else Serial.print(Bishop2);
        B++;
        break;
        
      case 'Q':
        Serial.print(Queen);
        break;
        
      case 'K':
        Serial.print(King);
        break;
        
      case 'P':
        switch(P) {
          case 0: Serial.print(Pawn1); break;
          case 1: Serial.print(Pawn2); break;
          case 2: Serial.print(Pawn3); break;
          case 3: Serial.print(Pawn4); break;
          case 4: Serial.print(Pawn5); break;
          case 5: Serial.print(Pawn6); break;
          case 6: Serial.print(Pawn7); break;
          case 7: Serial.print(Pawn8); break;
          default: Serial.print(Pawn1); break;
        }  
        P++;
        break;
        
      case '1': print_empty(i,1); break;
      case '2': print_empty(i,2); break;
      case '3': print_empty(i,3); break;
      case '4': print_empty(i,4); break;
      case '5': print_empty(i,5); break;
      case '6': print_empty(i,6); break;
      case '7': print_empty(i,7); break;
      case '8': print_empty(i,8); break;
        
    }
//    if (c!='_') Serial.print(c);
  }
  Serial.print(" \r\n");
}


int i,j,k,l,m, len;
char c;


//const char start_board[] PROGMEM ={"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"};
const char empty_board[] PROGMEM ={"8/8/8/8/8/8/8/8"};
const char real_board[] PROGMEM ={"8/pppppppp/8/8/8/8/1PPPPPPP/RNBQKBNR"};
const char e2e4_board[] PROGMEM ={"rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR"};
const char d7d5_board[] PROGMEM = {"rnbqkbnr/ppp1pppp/8/3p4/8/4P3/PPPP1PPP/RNBQKBNR"};

const char before_conversion_board[] PROGMEM = {"8/7P/7K/8/7k/8/7p/8"};
const char after_conversion_board[] PROGMEM = {"7Q/8/7K/8/7k/8/7p/8"};

char cmd[] = "e2e4";
char board[64];
char empty_fields=0;
char leds[8];
long t_leds_updated=0;

void loop() {
  t = millis();

  // ---- update LED's states
  if (Serial.available()>=8) { // LED's state
    t_leds_updated = t;
    for(i=0;i<8;i++) {
      c=Serial.read();
      if (c!=leds[i]) {
        Serial.print("LED ");
        Serial.print(i);
        Serial.print(" changed from 0x");
        Serial.print(leds[i],HEX);
        Serial.print(" to 0x");
        Serial.println(c,HEX);
        leds[i]=c;
      }
    }
    // flush a buffer
    while (Serial.available()>0)
      c=Serial.read();
  }

  // send state of chessboard to PC via USB
  if (t>=T_send) {
    T_send = millis()+1000u;
    send_data( current_board );
  }  
  
  if (mySerial.available()>0) {
    c = mySerial.read();
    if (c=='t') {
      mySerial.print(t);
      mySerial.print("ms, ");
      mySerial.print(t/60000u);
      mySerial.print("min ");
      mySerial.print((float)(t%60000u)/(float)1000);
      mySerial.println("s ");
    }
    if ( (c=='s')||(c=='l') ) {
      //mySerial.println(current_board);
      show_board();
      mySerial.print("LED's: ");
      for (i=0;i<8;i++) {mySerial.print(leds[i],HEX);mySerial.print(" ");}
      mySerial.println(" ");
    }
    if (c=='r') {
      reset_board();
      mySerial.println("I have reset board to initial state:");
      show_board();
    }

    if (c=='z') {
      set_error2_board();
      mySerial.println("I have set board to error2.sav state:");
      show_board();
    }

    
    if ( (c>=97)&&(c<=104) ) { // a...h
      cmd[0]=c;
      while (mySerial.available()<3); // wait for full 4 chars command
      for (i=0;i<3;i++) cmd[i+1]=mySerial.read();
      mySerial.print("\tI got a command == ");
      mySerial.println( cmd );
      
      // convert current_board to temporary format
      k=0;
      len = strlen( current_board);
      for(i=0;i<len;i++) {
        c = current_board[i];
        if ((c>=0x30)and(c<=0x39)) {
          for(j=0;j<(c-0x30);j++) board[k++]='.';
        }
        else if (c=='/') { j=0;} //nothing
        else { board[k++]=c; }
      }
      mySerial.println( "converted board before move:");
      mySerial.println( board );

      //do move
      i = (8-cmd[1]+0x30)*8+(cmd[0]-97); // from
      j = (8-cmd[3]+0x30)*8+(cmd[2]-97); // to
      c = board[i];
      board[i]='.';
      board[j]=c;
      
      mySerial.println( i);
      mySerial.println( "*****");
      mySerial.println( j);
      
      mySerial.println( "converted board after move:");
      mySerial.println( board );

      k=0;
      l=0;
      for(i=0;i<8;i++) {   // rows
        for(j=0;j<8;j++) { // columns
          c = board[i*8+j];          
          if (c=='.') {
            l++; // number of empty fields
          }
          else {
            if (l>0) current_board[k++] = 0x30 + l; // number of empty places            
            l=0;
            current_board[k++] = c;
          }
        }
        if (l>0) current_board[k++] = 0x30 + l; // number of empty places
        if (i!=7) current_board[k++] = '/';
        l=0;
      }
      current_board[k]=0; // end of string

      show_board();


      // flush a buffer
      while (mySerial.available()>0)
        c=mySerial.read();
    }
  }

//  j++;
//  mySerial.println(j);
//  mySerial.println("Hello!");
//  delay(1000);


  
//  if ( !digitalRead(button_pin ) )  // pressed a button
      // read the value from the sensor:
//      a = analogRead(pot_pin);    
  
  
//  Serial.print("\npot_value = " );                       
//  Serial.print(pot_value);      
//  Serial.print("\tbutton = " );                       
//  Serial.print(digitalRead(button_pin));      
  //Serial.println(a);                       


//  if ( (a>5)&&(a<=118)   ) {
    //Serial.println("\n\nEmpty board");
//    send_data( empty_board );
//  }
//  if ( (a>118)&&(a<=247) ) {
    //Serial.println("\n\Start board");
//    send_data( start_board );
//  }
//  if ( (a>247)&&(a<=389) ) send_data( e2e4_board );
//  if ( (a>389)&&(a<=455) ) send_data( d7d5_board );
  
//  if ( (a>990) ) send_data( after_conversion_board );
//  if ( (a>858)&&(a<=990) ) send_data( before_conversion_board );
  
//  Serial.println(a);

  
//    len = strlen_P( real_board );
//    for( i=0; i<len; i++) {
//    c = pgm_read_byte_near( real_board + i );
//    if (c!='-') Serial.print(c);
//    }

  delay(2); // for ADC
}
