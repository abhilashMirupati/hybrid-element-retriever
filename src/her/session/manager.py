# PLACE THIS FILE AT: src/her/session/manager.py

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, sid):
        self.sessions[sid] = {}

    def get(self, sid):
        return self.sessions.get(sid)

    def destroy(self, sid):
        if sid in self.sessions:
            del self.sessions[sid]
