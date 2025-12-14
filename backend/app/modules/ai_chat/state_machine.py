"""
State machine for chatbot conversation flow.
Manages state transitions based on user interactions and task status.
"""

from app.modules.ai_chat.schemas import ChatState


class ChatStateMachine:
    """Simple state machine for chatbot conversations."""

    @staticmethod
    def get_initial_state() -> ChatState:
        """Get initial state for a new conversation."""
        return ChatState.IDLE

    @staticmethod
    def transition_to_explaining_task() -> ChatState:
        """Transition to explaining a task."""
        return ChatState.EXPLAINING_TASK

    @staticmethod
    def transition_to_waiting_confirmation() -> ChatState:
        """Transition to waiting for user confirmation."""
        return ChatState.WAITING_CONFIRMATION

    @staticmethod
    def transition_to_task_completed() -> ChatState:
        """Transition after task is completed."""
        return ChatState.TASK_COMPLETED

    @staticmethod
    def transition_to_error(error_message: str | None = None) -> ChatState:
        """Transition to error state."""
        return ChatState.ERROR

    @staticmethod
    def transition_to_idle() -> ChatState:
        """Transition back to idle state."""
        return ChatState.IDLE

    @staticmethod
    def can_transition_from(current_state: ChatState, target_state: ChatState) -> bool:
        """
        Check if transition from current_state to target_state is valid.

        Args:
            current_state: Current state
            target_state: Target state

        Returns:
            True if transition is valid
        """
        # Define valid transitions
        valid_transitions: dict[ChatState, list[ChatState]] = {
            ChatState.IDLE: [
                ChatState.EXPLAINING_TASK,
                ChatState.ERROR,
            ],
            ChatState.EXPLAINING_TASK: [
                ChatState.WAITING_CONFIRMATION,
                ChatState.TASK_COMPLETED,
                ChatState.IDLE,
                ChatState.ERROR,
            ],
            ChatState.WAITING_CONFIRMATION: [
                ChatState.TASK_COMPLETED,
                ChatState.EXPLAINING_TASK,
                ChatState.IDLE,
                ChatState.ERROR,
            ],
            ChatState.TASK_COMPLETED: [
                ChatState.IDLE,
                ChatState.EXPLAINING_TASK,
                ChatState.ERROR,
            ],
            ChatState.ERROR: [
                ChatState.IDLE,
                ChatState.EXPLAINING_TASK,
            ],
        }

        allowed = valid_transitions.get(current_state, [])
        return target_state in allowed
