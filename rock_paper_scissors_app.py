import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import av
import cv2
import mediapipe as mp
import random

def show_home_page():
    st.title('My Photo')
    st.image('img/Lobanov_A_N.jpg', use_column_width=True)

# Инициализация MediaPipe Hands только один раз
mp_hands = mp.solutions.hands

class VideoProcessor(VideoTransformerBase):
    def __init__(self):
        self.hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.last_hand_move = None

    def get_hand_move(self, hand_landmarks):
        landmarks = hand_landmarks.landmark
        if all([landmarks[i].y < landmarks[i+3].y for i in range(9, 20, 4)]): 
            return "rock" 
        elif landmarks[13].y < landmarks[16].y and landmarks[17].y < landmarks[20].y: 
            return "scissors" 
        else: 
            return "paper"

#    def getHandMove(hand_landmarks):
#        landmarks = hand_landmarks.landmark 
#        if all([landmarks[i].y < landmarks[i+3].y for i in range(9, 20, 4)]): 
#            return "rock" 
#        elif landmarks[13].y < landmarks[16].y and landmarks[17].y < landmarks[20].y: 
#            return "scissors" 
#        else: 
#            return "paper"

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")
        results = self.hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp.solutions.drawing_utils.draw_landmarks(
                    image, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )
                self.last_hand_move = self.get_hand_move(hand_landmarks)
        
        annotated_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        return av.VideoFrame.from_ndarray(annotated_image, format="bgr24")

def show_game_page():
    st.title('Rock Paper Scissors Game')
    st.write("Position your hand in front of the camera to choose your move.")

    # Define the function to simulate the computer's move
    def computer_move():
        moves = ['rock', 'paper', 'scissors']
        return random.choice(moves)

    # Define the function to process a round of the game
    def play_round(player_move, comp_move):
        if player_move == comp_move:
            return 'It is a draw!', 0
        elif (player_move == 'rock' and comp_move == 'scissors') or \
             (player_move == 'paper' and comp_move == 'rock') or \
             (player_move == 'scissors' and comp_move == 'paper'):
            return 'You win!', 1
        else:
            return 'The computer wins!', -1

    if 'player_score' not in st.session_state:
        st.session_state['player_score'] = 0
    if 'computer_score' not in st.session_state:
        st.session_state['computer_score'] = 0
    if 'last_hand_move' not in st.session_state:
        st.session_state['last_hand_move'] = None

    webrtc_ctx = webrtc_streamer(
        key="example",
        video_processor_factory=VideoProcessor,
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )

    # Button to start the game round
    if st.button('Play'):
        if webrtc_ctx.video_processor:
            last_move = webrtc_ctx.video_processor.last_hand_move
            if last_move:
                comp_move = computer_move()
                result_message, score = play_round(last_move, comp_move)
                st.session_state['player_score'] += max(score, 0)
                st.session_state['computer_score'] += max(-score, 0)
                st.write(f"Your move: {last_move}")
                st.write(f"Computer's move: {comp_move}")
                st.write(result_message)
            else:
                st.write("Please make a move in front of the camera.")

    # Display current score
    st.write(f"Your score: {st.session_state['player_score']}")
    st.write(f"Computer's score: {st.session_state['computer_score']}")

    # Optionally, add a button to display the last detected hand move
    if st.button('Show Last Move'):
        if hasattr(webrtc_ctx.video_processor, 'last_hand_move'):
            last_move = webrtc_ctx.video_processor.last_hand_move
            if last_move:
                st.write('Last detected move:', last_move)
            else:
                st.write('No move detected yet.')
        else:
            st.write('Video stream is not active.')

def main():
    # Create a sidebar for navigation
    st.sidebar.title('Navigation')
    page = st.sidebar.radio('Choose a page:', ['Home', 'Rock Paper Scissors Game'])

    # Display the selected page
    if page == 'Home':
        show_home_page()
    elif page == 'Rock Paper Scissors Game':
        show_game_page()

if __name__ == "__main__":
    main()