# TIMESTAMP START 2026-11-05T13:19:15+00:00 | REVISION R000044
"""Explicit installed-fastener contact policy; never relax solid tolerances."""
import re
import numpy as np
METAL=re.compile(r'\b(steel|metal|stainless|galvanized|brass|bronze|copper)\b',re.I)
RECEIVING=re.compile(r'wood|timber|pine|fir|cedar|bamboo|plywood|plytanium|sheathing|SmartSide|membrane|underlayment|roofing felt|CedarBreather|breather mat|adhesive tape|weatherstrip|elastomeric',re.I)
def intended_penetration(fastener,receiver):
    """Nails/screws may occupy only their declared wood/flexible receivers.

    Metal connectors, concrete, other fasteners and structural hardwood pins
    are not approved receivers under this rule. Those need matching geometry.
    """
    return bool((fastener.get('intentionalFastenerPenetration') or fastener.get('intentionalWoodPenetration')) and fastener.get('is_fastener') and fastener.get('fastenerKind') in ['nail','screw'] and METAL.search(fastener.get('material','')) and receiver['id'] in fastener.get('receiverIds',[]) and not receiver.get('is_fastener') and not METAL.search(receiver.get('material','')) and (receiver.get('is_timber') or RECEIVING.search(receiver.get('material',''))))
def contact_kind(a,b):
    return 'installed nail/screw receiving-material penetration' if intended_penetration(a,b) or intended_penetration(b,a) else None

def permitted_withdrawal(fastener,receiver,delta,receiver_delta=None):
    """Only the fastener can withdraw axially from an unmoving recipient.

    A board moving through a retained screw never gets this exemption. The
    planner must first withdraw its individual fasteners. Assembly is the
    reverse of this tested withdrawal, including normal wood displacement.
    """
    if not intended_penetration(fastener,receiver):return False
    # Static penetration can include a later covering touched by the nail
    # head. Only declared earlier recipients permit axial extraction.
    if receiver['id'] not in fastener.get('withdrawalReceiverIds',[]):return False
    move=np.asarray(delta,float);other=np.zeros(3) if receiver_delta is None else np.asarray(receiver_delta,float)
    if np.linalg.norm(other)>1e-14 or np.linalg.norm(move)<=1e-14:return False
    axis=np.asarray(fastener.get('withdrawal_direction') or fastener.get('installation',{}).get('withdrawalDirection') or [],float)
    if axis.shape!=(3,) or not np.isfinite(axis).all() or np.linalg.norm(axis)<=0:return False
    axis/=np.linalg.norm(axis);distance=float(move@axis)
    return distance>0 and np.linalg.norm(move-distance*axis)<=max(1e-12,1e-10*np.linalg.norm(move))
# TIMESTAMP END 2026-11-05T13:19:15+00:00 | REVISION R000044
