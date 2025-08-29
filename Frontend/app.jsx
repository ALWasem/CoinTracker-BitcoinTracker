const { useEffect, useState } = React;

const api = {
  async get(path){
    const r = await fetch(path);
    if(!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async post(path, body){
    const r = await fetch(path, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body||{}) });
    if(!r.ok) throw new Error(await r.text());
    return r.json();
  },
  async del(path){
    const r = await fetch(path, { method:'DELETE' });
    if(!r.ok) throw new Error(await r.text());
    return r.json();
  },
  listAddresses(){ return this.get('/addresses'); },
  addAddress(address){ return this.post('/addresses', { address }); },
  removeAddress(address){ return this.del(`/addresses/${encodeURIComponent(address)}`); },
  sync(address){ return this.post(`/sync/${encodeURIComponent(address)}`); },
  transactions(address){ return this.get(`/transactions/${encodeURIComponent(address)}`); },
};

function Status({text}){ if(!text) return null; return <div className="status">{text}</div>; }

function AddressRow({a, onView, onSync, onRemove}){
  return (
    <li className="list-row">
      <div className="left-info">
        <div className="addr-line mono muted text-xs truncate">{a.address}</div>
        <div className="text-xs" style={{marginTop:6}}>Balance: <span className="badge mono tabnums">{a.balance} BTC</span></div>
      </div>
      <div className="actions">
        <button className="btn" onClick={()=>onView(a.address)}>View Transaction</button>
        <button className="btn" onClick={()=>onSync(a.address)}>Sync</button>
        <button className="btn btn-danger" onClick={()=>onRemove(a.address)}>Remove</button>
      </div>
    </li>
  );
}

function Transactions({address}){
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);

  useEffect(()=>{
    if(!address){ setItems([]); return; }
    setLoading(true); setError('');
    api.transactions(address)
      .then(setItems)
      .catch(e=> setError(prettyError(e)))
      .finally(()=> setLoading(false));
  }, [address]);

  if(!address){ return <div className="muted text-sm">Select an address to view transactions.</div>; }
  if(loading) return <div className="muted text-sm">Loading transactions…</div>;
  if(error) return <div className="text-sm" style={{color:'#ef4444'}}>Error: {error}</div>;
  if(items.length === 0) return <div className="muted text-sm">No transactions</div>;

  return (
    <div style={{overflowX:'auto'}}>
      <table>
        <thead>
          <tr>
            <th>Time (UTC)</th>
            <th>Type</th>
            <th className="right">Amount (BTC)</th>
            <th>Tx Hash</th>
          </tr>
        </thead>
        <tbody>
          {items.map((t)=>{
            const ts = new Date(t.timestamp).toISOString().replace('T',' ').replace('Z',' UTC');
            return (
              <tr key={t.tx_hash}>
                <td>{ts}</td>
                <td className={t.type==='incoming' ? 'type-incoming' : 'type-outgoing'}>{t.type}</td>
                <td className="right mono">{t.amount}</td>
                <td className="mono muted truncate">{t.tx_hash}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function App(){
  const [addresses, setAddresses] = useState([]);
  const [selected, setSelected] = useState('');
  const [status, setStatus] = useState('');
  const [input, setInput] = useState('');

  const reload = () => {
    setStatus('Loading addresses…');
    api.listAddresses()
      .then(setAddresses)
      .catch(e => setStatus('Error: ' + prettyError(e)))
      .finally(() => setStatus(''));
  };

  useEffect(()=>{ reload(); }, []);

  const add = async () => {
    if(!input.trim()) return;
    setStatus('Adding…');
    try { await api.addAddress(input.trim()); setInput(''); reload(); }
    catch(e){ setStatus('Error: ' + prettyError(e)); }
  };

  const remove = async (address) => {
    setStatus('Removing…');
    try { await api.removeAddress(address); if(selected===address) setSelected(''); reload(); }
    catch(e){ setStatus('Error: ' + prettyError(e)); }
  };

  const sync = async (address) => {
    setStatus('Syncing…');
    try { await api.sync(address); reload(); if(selected===address) setSelected(address); setStatus('Synced ✓'); setTimeout(()=>setStatus(''), 800); }
    catch(e){ setStatus('Sync failed: ' + prettyError(e)); }
  };

  return (
    <div className="grid-layout">
      <section className="panel">
        <div className="section-title">Addresses</div>
        <div className="section-body">
          <div className="btn-wrap" style={{alignItems:'center', marginBottom:12}}>
            <input value={input} onChange={e=>setInput(e.target.value)} type="text" placeholder="Enter BTC address" className="input" />
            <button onClick={add} className="btn btn-lg">Add</button>
          </div>
          <Status text={status} />
          <ul className="list">
            {addresses.length===0 && (<li className="muted text-sm" style={{padding:'8px 0'}}>No addresses yet</li>)}
            {addresses.map(a => (
              <AddressRow key={a.address} a={a} onView={setSelected} onSync={sync} onRemove={remove} />
            ))}
          </ul>
        </div>
      </section>

      <section className="panel">
        <div className="section-title">Transactions</div>
        <div className="section-body">
          <Transactions address={selected} />
        </div>
      </section>
    </div>
  );
}

function prettyError(e){
  try { const j = JSON.parse(e.message); return j.error || e.message; } catch { return e.message||String(e); }
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
