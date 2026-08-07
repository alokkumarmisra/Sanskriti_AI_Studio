# Script to fix the router.py file by adding Message class if missing
import os

router_path = 'd:\\Sanskriti_AI_Studio\\ai_agents\\communication_bus\\router.py'

with open(router_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Check if Message class exists
if 'class Message:' not in content and '@dataclass\nclass RoutingConfig:' in content:
    print("Message class is missing! Adding it now...")
    
    # Message class to add
    message_class = '''
@dataclass
class Message:
    """Message class for inter-agent communication."""
    
    source_agent: str
    destination_agent: List[str]
    message_id: str = field(default_factory=lambda: f"msg_{datetime.now(timezone.utc).timestamp()}")
    task_id: str = ""
    milestone_id: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""
    priority: int = 2  # MEDIUM default
    
    message_type: str = "EVENT"  # EVENT, REQUEST, RESPONSE, ERROR
    
    retry_count: int = 0
    
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    @classmethod
    def create_request(cls, source_agent: str, destination_agent: List[str], **kwargs) -> "Message":
        """Create a request message."""
        return cls(
            source_agent=source_agent,
            destination_agent=destination_agent,
            message_type="REQUEST",
            **{k: v for k, v in kwargs.items() if k != 'message_type'},
        )
    
    @classmethod
    def create_response(cls, source_agent: str, destination_agent: List[str], **kwargs) -> "Message":
        """Create a response message."""
        return cls(
            source_agent=source_agent,
            destination_agent=destination_agent,
            message_type="RESPONSE",
            **{k: v for k, v in kwargs.items() if k != 'message_type'},
        )
    
    @classmethod
    def create_error(cls, source_agent: str, destination_agent: List[str], **kwargs) -> "Message":
        """Create an error message."""
        return cls(
            source_agent=source_agent,
            destination_agent=destination_agent,
            message_type="ERROR",
            **{k: v for k, v in kwargs.items() if k not in ('message_type', 'error_type', 'error_message')},
            error_type=kwargs.get('error_type'),
            error_message=kwargs.get('error_message'),
        )

'''
    
    # Replace the pattern - add Message class before RoutingConfig
    new_content = content.replace('@dataclass\nclass RoutingConfig:', message_class + '@dataclass\nclass RoutingConfig:')
    
    with open(router_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("Message class added successfully!")
else:
    print("Message class already exists or different issue.")
