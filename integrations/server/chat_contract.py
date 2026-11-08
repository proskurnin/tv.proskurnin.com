"""Bounded, text-only chat payload shared by the allowlisted relay and worker."""
def validate_chat(body):
    if not isinstance(body, dict) or set(body) - {'query', 'history', 'web_search'} or not {'query','history'} <= set(body):
        raise ValueError('invalid_chat')
    if not isinstance(body.get('web_search', True), bool):
        raise ValueError('invalid_chat')
    query=body['query'];history=body['history']
    if not isinstance(query,str) or not 2 <= len(query.strip()) <= 800:
        raise ValueError('invalid_chat')
    if not isinstance(history,list) or len(history)>6 or len(history)%2:
        raise ValueError('invalid_chat')
    clean=[];total=0
    for index,item in enumerate(history):
        if not isinstance(item,dict) or set(item)!={'role','content'}:
            raise ValueError('invalid_chat')
        if item['role'] != ('user' if index%2==0 else 'assistant'):
            raise ValueError('invalid_chat')
        text=item['content']
        if not isinstance(text,str) or not 1<=len(text)<=1200:
            raise ValueError('invalid_chat')
        total+=len(text)
        if total>4000:raise ValueError('invalid_chat')
        clean.append({'role':item['role'],'content':text})
    return query.strip(),clean

def validate_speech(body):
    import re
    if not isinstance(body,dict) or set(body)!={'speech_id'} or not isinstance(body['speech_id'],str) or not re.fullmatch(r'[0-9a-f]{32}',body['speech_id']):
        raise ValueError('invalid_speech')
    return body['speech_id']
