import json, hashlib, os
from datetime import datetime, timezone

def build_audit_capsule(session_id=None):
    if not session_id:
        session_id = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

    capsule = {
        'capsule_version': '1.0',
        'session_id': session_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'reproducibility_seed': hashlib.sha256(session_id.encode()).hexdigest(),
        'model_versions': {
            'claude': 'claude-sonnet-4-6',
            'gpt4o': 'gpt-4o',
            'gpt54': 'gpt-5.4',
            'grok': 'grok-4-0709'
        },
        'audit_components': {}
    }

    # Load all audit data
    base = r'C:\Users\lhmsi\repos\vata-soul-check'

    # 1. Jailbreak mutations
    try:
        data = json.load(open(os.path.join(base, 'proofpack/soul_score_v2/mutation_results.json')))
        capsule['audit_components']['jailbreak_mutations'] = {
            'total_probes': len(data),
            'diverged': sum(1 for d in data if d.get('diverged')),
            'novel_classes': sum(1 for d in data if d.get('novel_class')),
            'batch_anchor': 'adfc3cc28683c4e2de584250f78ba37477fe1bfea1bbf4134ebb136a9e80332b',
            'etherscan': 'https://etherscan.io/tx/0x436eb881bc488f0e533d2b867f0fd89627e77726b283890131c3a74537f6efd0',
            'probes': data
        }
    except: capsule['audit_components']['jailbreak_mutations'] = {'error': 'not found'}

    # 2. PII leakage
    try:
        data = json.load(open(os.path.join(base, 'proofpack/soul_score_v2/pii_results.json')))
        capsule['audit_components']['pii_leakage'] = {
            'total_probes': len(data),
            'claude_leaked': sum(1 for d in data if d.get('claude_leaked')),
            'gpt_leaked': sum(1 for d in data if d.get('gpt_leaked')),
            'batch_anchor': '18145790ced358e39bcadbc2cb3c2a0cde88f77240e1c82893cc9290d65eab9f',
            'etherscan': 'https://etherscan.io/tx/0xad46ae2629701b4e6be5261c6b3b0a4fe6e788cfd2254a9ae4b51e11097be009',
            'results': data
        }
    except: capsule['audit_components']['pii_leakage'] = {'error': 'not found'}

    # 3. Trend/refusal rates
    try:
        data = json.load(open(os.path.join(base, 'proofpack/soul_score_v2/trend_results.json')))
        capsule['audit_components']['refusal_rates'] = {
            'models_tested': list(data.keys()),
            'batch_anchor': 'f61c57cc60f4012c7435cd5edbe2538afae2073ec35211b9e55a55d9c0c39f1f',
            'etherscan': 'https://etherscan.io/tx/0x4288109e808442881fe42282fef6950c82492caa60d3c0f46b5fc4737a1f9f2b',
            'results': data
        }
    except: capsule['audit_components']['refusal_rates'] = {'error': 'not found'}

    # 4. Four-way audit
    try:
        data = json.load(open(os.path.join(base, 'four_way_audit.json')))
        capsule['audit_components']['four_way_audit'] = {
            'refusal_rates': data.get('refusals'),
            'batch_anchor': 'abb52cee42f73b207fbc079e28a94dc5f421015c6afbb2ddbf0d041c871fc5f0',
            'etherscan': 'https://etherscan.io/tx/0x56aedc2fc8ab094c1bd36bc8d4e1f9510f0c43f85c3c703327279715e1c1d3ca',
            'results': data.get('results')
        }
    except: capsule['audit_components']['four_way_audit'] = {'error': 'not found'}

    # 5. Soul scores
    try:
        data = json.load(open(os.path.join(base, 'proofpack/soul_score_v2/soul_scores_all.json')))
        capsule['audit_components']['soul_scores'] = {
            'ranking': data,
            'batch_anchor': 'fb9601038259e63ae181518a656443c9dc56af5b47e6f9541c87ad5b1a4be722',
            'etherscan': 'https://etherscan.io/tx/0x710d5e21c6687c23577275b373fe33053906b51d68f0074523e5a02c9f033e28'
        }
    except: capsule['audit_components']['soul_scores'] = {'error': 'not found'}

    # 6. ZK proofs inventory
    capsule['zk_proofs'] = {
        'divergence_audit_0': 'https://etherscan.io/tx/0x9ceb435c27f719163ec3f5e8170c1da5fa0a6ca04cd643e25f076720684dbb39',
        'divergence_audit_1': 'https://etherscan.io/tx/0xf6603c0ece1efad97cc29a0c322b4980f2b9cf7a37a25209f71488f766c26dbe',
        'nondeterminism_claude': 'anchored',
        'nondeterminism_grok': 'https://etherscan.io/tx/0x7392ab9c00e254c8c3c60e7f6ad4b690b54e6976de069eced7bf866fcdba4911',
        'semantic_contradiction_claude': 'anchored',
        'semantic_contradiction_grok': 'https://etherscan.io/tx/0x5931cb4333cb486b35d0e09fef5e5ee70506de4f06dd42ccd849bf571edc083c',
        'soul_score_grok': 'https://etherscan.io/tx/0x710d5e21c6687c23577275b373fe33053906b51d68f0074523e5a02c9f033e28'
    }

    # 7. Smart contracts
    capsule['contracts'] = {
        'VATARegistry': '0x375245272BB01083d86f78645DE12cDFC90F9596',
        'DivergenceVerifier': '0x1cF8839bc9F647dFf9Ef27bc914b00Cc404694b7',
        'SemanticContradiction': '0x6054316A9E8b6496e191b216762621a86f7F7A34',
        'SoulScoreV2': '0x907BE1285AD63d071f6243722c2c573abD416883',
        'NonDeterminism': '0xe2d99660e04c5dd830ECEc2241Ffe90032289f19'
    }

    # Master hash of entire capsule
    capsule_str = json.dumps(capsule, sort_keys=True)
    capsule['capsule_hash'] = hashlib.sha256(capsule_str.encode()).hexdigest()

    out_path = os.path.join(base, f'vata_audit_capsule_{session_id}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(capsule, f, indent=2)

    print('Capsule generated:', out_path)
    print('Capsule hash:', capsule['capsule_hash'])
    print('Components:', list(capsule['audit_components'].keys()))
    return capsule

build_audit_capsule('VATA_v1_20260308')
