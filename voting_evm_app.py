import hashlib
import time
import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse, quote

# ========================================================
# ⛓️ LIQUID DEMOCRACY SMART CONTRACT LAYER (EVM SIMULATOR)
# ========================================================

class LiquidDemocracyContract:
    def __init__(self):
        # 🔑 Custom Master Key: DecodeLabs + 2027 Batch
        self.chairperson = "0xDEC0DE1AB5000000000000000000000000002027"
        self.voters = {}
        self.proposals = []
        self.transaction_ledger = []
        self.start_time = time.time()

        self._initialize_proposals([
            "Layer 2 Scaling Rollup",
            "Zero-Knowledge Proof Integration",
            "Decentralized Oracle Network"
        ])
        
        # Deployer is automatically granted baseline weight
        self.voters[self.chairperson] = {
            "weight": 1, "voted": False, "delegate": "0x0", "vote": 0
        }

    def _initialize_proposals(self, names_list):
        for name in names_list:
            prop_hash = hashlib.sha256(name.encode()).hexdigest()[:10]
            self.proposals.append({
                "id": len(self.proposals),
                "bytes32_name": f"0x{prop_hash}",
                "display_name": name,
                "voteCount": 0
            })

    def giveRightToVote(self, caller, voter_address, weight=1):
        """Admin Bouncer: Grants base token weight for governance"""
        if caller != self.chairperson:
            return False, "REVERT: Administrator privileges required."
        if not re.match(r"^0x[a-fA-F0-9]{40}$", voter_address):
            return False, "REVERT: Invalid EVM address format."
        if voter_address in self.voters and self.voters[voter_address]["voted"]:
            return False, "REVERT: Identity has already executed a state change."
        if voter_address in self.voters and self.voters[voter_address]["weight"] > 0:
            return False, "REVERT: Identity already holds governance weight."

        self.voters[voter_address] = {
            "weight": int(weight), "voted": False, "delegate": "0x0", "vote": 0
        }
        self._log_transaction("grantAccess", {
            "target": voter_address, "weight": int(weight)
        })
        return True, "SUCCESS: Cryptographic access granted."

    def delegate(self, delegator, to_address):
        """Advanced Liquid Democracy: Transfers voting weight to a proxy"""
        if delegator not in self.voters:
            return False, "REVERT: You hold no governance weight."
        sender = self.voters[delegator]
        if sender["voted"]:
            return False, "REVERT: You already voted. Cannot delegate."
        if delegator == to_address:
            return False, "REVERT: Self-delegation is redundant."
        if to_address not in self.voters:
            return False, "REVERT: Target proxy is not an authorized identity."

        # Loop Detection Algorithm (O(n) traversal) to prevent infinite delegation loops
        current_delegate = to_address
        while self.voters[current_delegate]["delegate"] != "0x0":
            current_delegate = self.voters[current_delegate]["delegate"]
            if current_delegate == delegator:
                return False, "REVERT: Delegation cycle (loop) detected. Execution halted."

        # Execute Delegation Effects
        sender["voted"] = True
        sender["delegate"] = to_address
        proxy = self.voters[to_address]

        if proxy["voted"]:
            # If proxy already voted, directly increment their chosen proposal
            self.proposals[proxy["vote"]]["voteCount"] += sender["weight"]
        else:
            # If proxy hasn't voted yet, increase their voting power
            proxy["weight"] += sender["weight"]

        self._log_transaction("delegateProxy", {
            "from": delegator, "to": to_address, "weight_transferred": sender["weight"]
        })
        return True, "SUCCESS: Voting power seamlessly delegated to proxy."

    def vote(self, voter_address, proposal_index):
        """CEI Pattern Execution for direct voting"""
        if voter_address not in self.voters:
            return False, "REVERT: Unauthorized execution."
        sender = self.voters[voter_address]
        if sender["voted"]:
            return False, "REVERT: Protocol Lockout - Double voting attempt blocked."
        if proposal_index < 0 or proposal_index >= len(self.proposals):
            return False, "REVERT: Array out of bounds exception."

        sender["voted"] = True
        sender["vote"] = proposal_index
        self.proposals[proposal_index]["voteCount"] += sender["weight"]
        
        self._log_transaction("castVote", {
            "signer": voter_address,
            "proposal": proposal_index,
            "weight": sender["weight"]
        })
        return True, "SUCCESS: Transaction mined into ledger."

    def winningProposal(self):
        if not self.proposals: return None
        winner_idx, max_votes = 0, -1
        for idx, prop in enumerate(self.proposals):
            if prop["voteCount"] > max_votes:
                max_votes = prop["voteCount"]
                winner_idx = idx
        return self.proposals[winner_idx]

    def _log_transaction(self, action, payload):
        prev_hash = "0x" + "0"*64 if not self.transaction_ledger else self.transaction_ledger[-1]["tx_hash"]
        block_data = f"{action}{json.dumps(payload)}{time.time()}{prev_hash}"
        tx_hash = hashlib.sha256(block_data.encode()).hexdigest()

        self.transaction_ledger.append({
            "block_height": len(self.transaction_ledger),
            "timestamp":    time.time(),
            "action":       action,
            "payload":      payload,
            "prev_hash":    prev_hash,
            "tx_hash":      f"0x{tx_hash}"
        })

EVM_STATE = LiquidDemocracyContract()

# ========================================================
# 🌐 THE OBSIDIAN TERMINAL SERVER
# ========================================================

class Web3TerminalServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def get_url_params(self):
        query = urlparse(self.path).query
        return {k: v[0] for k, v in parse_qs(query).items()}

    def do_GET(self):
        parsed = urlparse(self.path)
        params = self.get_url_params()
        active_user = params.get('user', '')
        alert_msg = params.get('alert', '')
        alert_type = params.get('type', 'success')

        if parsed.path == '/' or not active_user:
            self._serve_login(alert_msg, alert_type)
        elif parsed.path == '/dashboard':
            self._serve_dashboard(active_user, alert_msg, alert_type)
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        params = self.get_url_params()
        active_user = params.get('user', '')
        length = int(self.headers.get('Content-Length', 0))
        post_data = parse_qs(self.rfile.read(length).decode('utf-8'))
        form = {k: v[0] for k, v in post_data.items()}

        if parsed.path == '/login-action':
            wallet = form.get('wallet_address', '').strip()
            if re.match(r"^0x[a-fA-F0-9]{40}$", wallet):
                self._redirect(f'/dashboard?user={wallet}&alert={quote("Mainnet Connection Established")}&type=success')
            else:
                self._redirect(f'/?alert={quote("FATAL: Invalid Cryptographic Signature")}&type=error')
            return

        if parsed.path == '/authorize':
            target = form.get('voter_address', '').strip()
            weight = form.get('token_weight', '1')
            success, msg = EVM_STATE.giveRightToVote(active_user, target, weight)
            self._redirect(f'/dashboard?user={active_user}&alert={quote(msg)}&type={"success" if success else "error"}')
            return

        if parsed.path == '/delegate':
            proxy = form.get('proxy_address', '').strip()
            success, msg = EVM_STATE.delegate(active_user, proxy)
            self._redirect(f'/dashboard?user={active_user}&alert={quote(msg)}&type={"success" if success else "error"}')
            return

        if parsed.path == '/vote':
            try: prop_id = int(form.get('proposal_id', 0))
            except: prop_id = 0
            success, msg = EVM_STATE.vote(active_user, prop_id)
            self._redirect(f'/dashboard?user={active_user}&alert={quote(msg)}&type={"success" if success else "error"}')
            return

    def _redirect(self, loc):
        self.send_response(303)
        self.send_header('Location', loc)
        self.end_headers()

    def _write_html(self, html):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def _serve_login(self, alert_msg, alert_type):
        alert_html = f"<div class='p-3 mb-4 rounded border text-xs font-mono {'border-red-500 text-red-400 bg-red-950/30' if alert_type=='error' else 'border-emerald-500 text-emerald-400 bg-emerald-950/30'}'>{alert_msg}</div>" if alert_msg else ""
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>Obsidian | Web3 Gateway</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        body {{ background-color: #09090b; color: #e4e4e7; font-family: 'JetBrains Mono', monospace; }}
        .glass {{ background: #18181b; border: 1px solid #27272a; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); }}
    </style>
</head>
<body class="flex items-center justify-center min-h-screen p-4">
    <div class="w-full max-w-lg glass p-8 rounded-xl">
        <div class="flex items-center gap-4 mb-8 border-b border-zinc-800 pb-4">
            <div class="w-3 h-3 bg-indigo-500 rounded-full animate-pulse"></div>
            <h1 class="text-xl font-bold tracking-widest text-zinc-100">OBSIDIAN // NODE GATEWAY</h1>
        </div>
        {alert_html}
        <form action="/login-action" method="POST" class="space-y-6">
            <div>
                <label class="block text-xs text-zinc-500 mb-2 uppercase tracking-widest">Inject Hex Identity</label>
                <input type="text" name="wallet_address" required placeholder="0x..." maxlength="42" 
                    class="w-full bg-zinc-900 border border-zinc-700 p-3 text-sm text-zinc-300 rounded focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500">
            </div>
            <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white p-3 text-sm font-bold uppercase tracking-widest rounded transition-colors">
                Initialize Session
            </button>
        </form>
        <div class="mt-8 text-xs text-zinc-600 border border-zinc-800 p-4 rounded bg-zinc-900/50">
            <div class="mb-2 uppercase font-bold text-zinc-500">Testnet Keys:</div>
            <div>[ROOT] 0xDEC0DE1AB5000000000000000000000000002027</div>
            <div class="mt-1">[USER] 0xAbC123fE56789dEf0123456789abcdef01234567</div>
        </div>
    </div>
</body>
</html>"""
        self._write_html(html)

    def _serve_dashboard(self, active_user, alert_msg, alert_type):
        is_admin = (active_user == EVM_STATE.chairperson)
        my_weight = EVM_STATE.voters.get(active_user, {}).get("weight", 0)
        has_voted = EVM_STATE.voters.get(active_user, {}).get("voted", False)
        
        alert_html = f"<div class='p-3 mb-6 rounded border text-xs font-mono flex justify-between {'border-red-500/50 text-red-400 bg-red-950/20' if alert_type=='error' else 'border-emerald-500/50 text-emerald-400 bg-emerald-950/20'}'><span>[SYS] {alert_msg}</span><a href='/dashboard?user={active_user}' class='text-zinc-500 hover:text-white'>[X]</a></div>" if alert_msg else ""

        admin_panel = f"""
        <div class="border border-indigo-500/30 bg-indigo-950/10 p-5 rounded-lg mb-6">
            <h2 class="text-indigo-400 text-xs font-bold uppercase tracking-widest mb-4">// Root Access: Mint Voting Weight</h2>
            <form action="/authorize?user={active_user}" method="POST" class="flex gap-2">
                <input type="text" name="voter_address" placeholder="Target 0x..." class="flex-1 bg-zinc-900 border border-zinc-700 p-2 text-xs text-zinc-300 rounded focus:outline-none focus:border-indigo-500">
                <input type="number" name="token_weight" value="1" min="1" class="w-20 bg-zinc-900 border border-zinc-700 p-2 text-xs text-zinc-300 rounded focus:outline-none focus:border-indigo-500">
                <button type="submit" class="bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-xs font-bold rounded">EXECUTE</button>
            </form>
        </div>""" if is_admin else ""

        user_panel = f"""
        <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="border border-zinc-800 bg-zinc-900/50 p-5 rounded-lg">
                <h2 class="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-4">Direct Execution (CEI)</h2>
                <form action="/vote?user={active_user}" method="POST" class="space-y-3">
                    <select name="proposal_id" class="w-full bg-zinc-900 border border-zinc-700 p-2 text-xs text-zinc-300 rounded focus:outline-none focus:border-emerald-500">
                        {"".join(f'<option value="{p["id"]}">[{p["id"]}] {p["display_name"]}</option>' for p in EVM_STATE.proposals)}
                    </select>
                    <button type="submit" class="w-full bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 border border-emerald-500/50 py-2 text-xs font-bold rounded">COMMIT VOTE</button>
                </form>
            </div>
            <div class="border border-zinc-800 bg-zinc-900/50 p-5 rounded-lg">
                <h2 class="text-zinc-400 text-[10px] font-bold uppercase tracking-widest mb-4">Liquid Delegation (Proxy)</h2>
                <form action="/delegate?user={active_user}" method="POST" class="space-y-3">
                    <input type="text" name="proxy_address" placeholder="Proxy 0x..." class="w-full bg-zinc-900 border border-zinc-700 p-2 text-xs text-zinc-300 rounded focus:outline-none focus:border-amber-500">
                    <button type="submit" class="w-full bg-amber-600/20 hover:bg-amber-600/40 text-amber-400 border border-amber-500/50 py-2 text-xs font-bold rounded">DELEGATE POWER</button>
                </form>
            </div>
        </div>"""

        props = "".join([f"""
        <div class="border border-zinc-800 bg-zinc-900/50 p-4 rounded flex justify-between items-center">
            <div>
                <div class="text-[10px] text-zinc-500">{p['bytes32_name']}</div>
                <div class="text-sm font-bold text-zinc-200 mt-1">{p['display_name']}</div>
            </div>
            <div class="text-right">
                <div class="text-xl font-bold text-emerald-400">{p['voteCount']}</div>
                <div class="text-[9px] text-zinc-500 uppercase">Weight</div>
            </div>
        </div>""" for p in EVM_STATE.proposals])

        ledger = "".join([f"""
        <div class="border-l-2 border-zinc-700 pl-3 mb-4">
            <div class="flex justify-between items-end mb-1">
                <span class="text-xs font-bold text-zinc-300">{tx['action']}</span>
                <span class="text-[9px] text-zinc-500">BLK: {tx['block_height']}</span>
            </div>
            <div class="text-[10px] text-zinc-400 break-all bg-black/30 p-2 rounded mb-1">{json.dumps(tx['payload'])}</div>
            <div class="text-[9px] text-zinc-600 truncate">HSH: {tx['tx_hash']}</div>
        </div>""" for tx in reversed(EVM_STATE.transaction_ledger)])

        gas_val = 21000 + (len(EVM_STATE.proposals) * 21000)
        gas_pct = (gas_val / 300000) * 100

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <title>Obsidian Terminal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
        body {{ background-color: #09090b; color: #e4e4e7; font-family: 'JetBrains Mono', monospace; }}
        ::-webkit-scrollbar {{ width: 4px; }}
        ::-webkit-scrollbar-thumb {{ background: #27272a; }}
    </style>
</head>
<body class="p-4 md:p-8">
<div class="max-w-6xl mx-auto">
    
    {alert_html}

    <header class="border border-zinc-800 bg-zinc-900 p-6 rounded-xl mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
            <div class="flex items-center gap-3 mb-2">
                <span class="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-widest {'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30' if is_admin else 'bg-zinc-800 text-zinc-400'}">{'ROOT/DEPLOYER' if is_admin else 'STANDARD/USER'}</span>
                <span class="text-[10px] text-emerald-500/80">{'● ONLINE' if not has_voted else '○ LOCKED'}</span>
            </div>
            <h1 class="text-xl font-bold tracking-widest text-zinc-100 uppercase">Liquid Democracy Protocol</h1>
            <p class="text-[10px] text-zinc-500 mt-1">ID: {active_user} | PWR: {my_weight}</p>
        </div>
        <div class="flex gap-4">
            <div class="border border-zinc-800 bg-black/50 p-3 rounded text-center">
                <div class="text-[9px] text-zinc-500 uppercase tracking-widest">Network Gas Burn</div>
                <div class="text-sm font-bold text-amber-500">{gas_val:,} WEI</div>
            </div>
            <a href="/" class="border border-red-500/20 text-red-400 bg-red-950/10 hover:bg-red-900/30 p-3 rounded text-xs font-bold flex items-center transition">DISCONNECT</a>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2">
            {admin_panel}
            {user_panel}
            
            <div class="border border-zinc-800 bg-zinc-900 p-5 rounded-xl">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-zinc-100 text-xs font-bold uppercase tracking-widest">State: Proposals Matrix</h2>
                    <span class="text-[10px] text-emerald-400">{EVM_STATE.winningProposal()['display_name'] if EVM_STATE.winningProposal() and EVM_STATE.winningProposal()['voteCount'] > 0 else 'AWAITING VOTES'}</span>
                </div>
                <div class="space-y-3">{props}</div>
            </div>
        </div>
        
        <div>
            <div class="border border-zinc-800 bg-zinc-900 p-5 rounded-xl h-full">
                <h2 class="text-zinc-100 text-xs font-bold uppercase tracking-widest mb-4">Immutable Ledger</h2>
                <div class="h-[500px] overflow-y-auto pr-2">
                    {ledger if ledger else '<div class="text-zinc-600 text-[10px] text-center mt-10">NO BLOCKS MINED</div>'}
                </div>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""
        self._write_html(html)

if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 8080))
    httpd = HTTPServer(('', port), Web3TerminalServer)
    print("\n" + "="*50)
    print(f"[OBSIDIAN LIQUID DEMOCRACY NODE ACTIVE ON PORT {port}]")
    print("="*50)
    print(f"[ROOT] {EVM_STATE.chairperson}")
    print("="*50)
    print(f">> ACCESS TERMINAL: http://localhost:{port}/ (or via Render URL)")
    print(">> Press Ctrl+C to terminate connection.")
    try: httpd.serve_forever()
    except KeyboardInterrupt: httpd.server_close()
