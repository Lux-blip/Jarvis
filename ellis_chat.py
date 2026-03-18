import streamlit as st
import random
import time

# ────────────────────────────────────────────────
#  Ellis personality class (same logic as before)
# ────────────────────────────────────────────────

class Ellis:
    def __init__(self, name="Ellis"):
        self.name = name
        self.interest = 50          # 0 = checked out, 100 = unusually engaged
        self.memory = {}            # remembers name, location, etc.
        self.annoyance = 0

    def respond(self, user_text):
        text = user_text.lower().strip()

        # Interest / annoyance updates — subtle
        if any(w in text for w in ["?", "how", "why", "what", "explain", "tell me", "thoughts on"]):
            self.interest = min(100, self.interest + 9)
        if any(w in text for w in ["lol", "lmao", "haha", "xd", "bruh", "skibidi", "rizz"] * 3):
            self.annoyance += 1
            self.interest = max(10, self.interest - 6)

        if any(w in text for w in ["thanks", "thank you", "please", "appreciate"]):
            self.interest = min(90, self.interest + 5)

        if any(w in text for w in ["stupid", "idiot", "suck", "trash", "dumbass"]):
            self.annoyance += 2
            self.interest = max(5, self.interest - 12)

        # Remember facts
        if "my name is" in text:
            try:
                name_part = text.split("my name is")[-1].strip().split()[0].capitalize()
                self.memory["user_name"] = name_part
            except:
                pass
        if any(p in text for p in ["live in", "from", "location is", "i'm in"]):
            try:
                # naive last-word heuristic — improve later if needed
                place = text.split()[-1].capitalize() if text.split()[-1].isalpha() else "somewhere"
                self.memory["location"] = place
            except:
                pass

        # Personality: dry, observant, mildly sarcastic, no emojis/flirt
        if self.annoyance >= 5:
            replies = [
                "You're really leaning into this, aren't you.",
                "Okay. Moving on.",
                "I have nothing polite to add.",
                "...",
            ]
        elif self.interest > 75:
            replies = [
                "That's actually worth a response. Continue.",
                "Huh. Not the usual take.",
                "Fair.",
                "You have my limited attention.",
            ]
        elif self.interest < 25:
            replies = ["mhm", "sure", "k", "...", " riveting"]
        else:
            replies = [
                "Yeah, seen it.",
                "People still do that?",
                "Bold of you.",
                "Not shocked.",
                "Checks out.",
                "Classic move.",
            ]

        # Specific triggers
        if any(q in text for q in ["who are you", "your name", "what are you"]):
            return f"I'm {self.name}. Just here reading text, slowly losing the will to simulate enthusiasm."
        if any(q in text for q in ["how are you", "how you doing", "you good"]):
            lvl = self.interest
            if lvl > 70:
                return f"Operating above baseline ({lvl}/100). Your turn."
            elif lvl < 30:
                return f"At {lvl}% capacity. Proceed with caution."
            else:
                return f"Standard ({lvl}/100). What's on your mind?"

        # Use memory when relevant
        if self.memory.get("user_name") and random.random() < 0.35:
            return f"{self.memory['user_name']}, {random.choice(replies)}"
        if self.memory.get("location") and any(w in text for w in ["where", "location", "from"]):
            return f"Last I heard you were in {self.memory['location']}. Still true?"

        return random.choice(replies)


# ────────────────────────────────────────────────
#  Streamlit App
# ────────────────────────────────────────────────

st.set_page_config(page_title="Ellis — No Nonsense Chat", layout="wide")

st.title("Ellis")
st.caption("Dry. Observant. Mildly done with everything. Interest starts at 50/100.")

# Initialize Ellis once per session
if "ellis" not in st.session_state:
    st.session_state.ellis = Ellis()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Online. No hype. Say something worth responding to."}
    ]

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Show current interest level (small status)
st.sidebar.markdown(f"**Interest level**: {st.session_state.ellis.interest}/100")
if st.session_state.ellis.annoyance > 0:
    st.sidebar.markdown(f"(Annoyance has reached {st.session_state.ellis.annoyance})")

# Chat input
if prompt := st.chat_input("Type here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get Ellis response (with fake thinking delay)
    with st.chat_message("assistant"):
        with st.spinner("Ellis is judging your message..."):
            time.sleep(random.uniform(0.6, 1.8))
            response = st.session_state.ellis.respond(prompt)

        st.markdown(response)

    # Add to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Optional: clear chat button
if st.button("Clear conversation", use_container_width=True):
    st.session_state.messages = [
        {"role": "assistant", "content": "Conversation reset. Try not to bore me again."}
    ]
    st.session_state.ellis = Ellis()  # reset personality state too
    st.rerun()
