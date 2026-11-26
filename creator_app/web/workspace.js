(() => {
  const TOKEN_KEY = "cknexus_access_token";
  const SESSION_KEY = "nexus_session_id";
  const $ = (s) => document.querySelector(s);
  function createSessionId() {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return "nexus-web-" + Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
  }
  const state = { agents: [], plugins: [], connectors: [], status: null, mcpQuery: "", mcpCursor: null, mcpCandidates: [], session: sessionStorage.getItem(SESSION_KEY) || createSessionId(), busy: false };
  const token = () => sessionStorage.getItem(TOKEN_KEY) || "";
  const headers = (json=false) => ({...(json?{"Content-Type":"application/json"}:{}),...(token()?{Authorization:"Bearer "+token()}:{})});
  const toast = (message) => { const el=$("#toast"); el.textContent=message; el.classList.add("show"); setTimeout(()=>el.classList.remove("show"),3000); };
  async function api(path, options={}) {
    const response=await fetch(path,{...options,headers:{...headers(Boolean(options.body)),...(options.headers||{})}});
    const data=await response.json().catch(()=>({}));
    if(!response.ok){const detail=data.detail||data;const error=new Error(detail.message||detail.error||"HTTP "+response.status);error.status=response.status;throw error;}
    return data;
  }
  function pluginStatusLabel(plugin){
    if(plugin.connected)return "CONNECTED";
    if(plugin.auth_method==="none")return "AVAILABLE";
    if(plugin.state==="READY_TO_CONNECT")return "READY TO CONNECT";
    if(plugin.state==="PREREQUISITE_REQUIRED")return "PREREQUISITE REQUIRED";
    if(plugin.state==="CONFIGURED_NOT_VERIFIED")return "CONFIGURED · NOT VERIFIED";
    return "SETUP REQUIRED";
  }
  function createPluginCard(plugin){
    const card=document.createElement("article");card.className="plugin-card";
    const head=document.createElement("div");head.className="plugin-card-head";
    const title=document.createElement("strong");title.textContent=plugin.name;
    const badge=document.createElement("span");badge.className="plugin-state "+(plugin.connected?"connected":"pending");badge.textContent=pluginStatusLabel(plugin);
    head.append(title,badge);
    const message=document.createElement("p");message.textContent=plugin.message||"Installed adapter";
    const meta=document.createElement("small");meta.textContent=[plugin.category,plugin.auth_method].filter(Boolean).join(" · ");
    card.append(head,message,meta);
    if(plugin.connect_action){
      const action=document.createElement("button");action.type="button";action.className="plugin-action";
      const connected=Boolean(plugin.connected);
      action.textContent=connected?"Connected":(plugin.connect_action==="open-youtube-player"?"Open YouTube":(plugin.connect_ready?(plugin.connect_action==="gmail-oauth"?"Connect Gmail":"Connect GitHub App"):"Setup required"));
      action.disabled=connected||(plugin.connect_action!=="open-youtube-player"&&!plugin.connect_ready);
      action.addEventListener("click",()=>performPluginAction(plugin,action));
      card.append(action);
    }
    return card;
  }
  function renderPluginCatalog(){
    const root=$("#plugin-list"),connectorsRoot=$("#connector-list");
    root.replaceChildren();connectorsRoot.replaceChildren();
    $("#plugin-count").textContent=state.plugins.length+" installed adapters · "+state.connectors.length+" registered connectors";
    if(!state.plugins.length){const empty=document.createElement("p");empty.className="muted";empty.textContent="ไม่พบปลั๊กอินที่ติดตั้งในระบบนี้";root.append(empty);}
    state.plugins.forEach(plugin=>root.append(createPluginCard(plugin)));
    if(!state.connectors.length){const empty=document.createElement("p");empty.className="muted";empty.textContent="ยังไม่มี MCP / API Connector ที่ลงทะเบียน";connectorsRoot.append(empty);}
    state.connectors.forEach(connector=>{
      const card=document.createElement("article");card.className="plugin-card";
      const head=document.createElement("div");head.className="plugin-card-head";
      const title=document.createElement("strong");title.textContent=connector.name;
      const badge=document.createElement("span");badge.className="plugin-state pending";badge.textContent=connector.state;
      head.append(title,badge);
      const message=document.createElement("p");message.textContent=connector.protocol.toUpperCase()+" · "+connector.tool_count+" tools · read-only "+connector.read_only_count+" · write "+connector.write_count;
      card.append(head,message);
      if(connector.can_discover){
        const action=document.createElement("button");action.type="button";action.className="plugin-action";action.textContent="Discover tools";
        action.addEventListener("click",async()=>{
          action.disabled=true;action.textContent="Discovering…";
          try{await api("/api/connectors/"+encodeURIComponent(connector.id)+"/discover",{method:"POST"});toast("ตรวจพบ Tools และบันทึก Schema Evidence แล้ว");await refreshPluginCatalog();}
          catch(error){toast("Discovery ถูกปฏิเสธหรือไม่สำเร็จ: "+error.message);action.disabled=false;action.textContent="Discover tools";}
        });
        card.append(action);
      }
      connectorsRoot.append(card);
    });
  }
  async function refreshPluginCatalog(){
    const root=$("#plugin-list");
    if(!root)return;
    try{
      const catalog=await api("/api/plugins");
      state.plugins=Array.isArray(catalog.plugins)?catalog.plugins.filter(item=>item.installed===true):[];
      state.connectors=Array.isArray(catalog.connectors)?catalog.connectors:[];
      renderPluginCatalog();
    }catch(error){
      state.plugins=[];state.connectors=[];
      root.replaceChildren();const message=document.createElement("p");message.className="muted";
      message.textContent=error.status===401?"ต้องตั้งค่า CK-NEXUS Access Token เพื่อดู Plugin Inventory":"โหลด Plugin Inventory ไม่สำเร็จ: "+error.message;
      root.append(message);$("#plugin-count").textContent="Inventory unavailable";
    }
  }
  async function performPluginAction(plugin,button){
    if(plugin.connect_action==="open-youtube-player"){
      const body=$("#music-body");if(body.hidden)$("#music-toggle").click();return;
    }
    button.disabled=true;
    try{
      if(plugin.connect_action==="gmail-oauth"){
        const gmail=await api("/api/integrations/gmail/status");
        if(!gmail.configured){toast("Gmail OAuth ยังไม่พร้อม: ต้องตั้งค่า Client ID, Client Secret และ Redirect URI ผ่าน Credential Broker");return;}
        if(gmail.token_persistence!=="encrypted-vault"){toast("ยังเชื่อม Gmail ไม่ได้: ต้องเปิด Encrypted Credential Vault ก่อน");return;}
        const result=await api("/api/integrations/gmail/oauth/start");
        const target=new URL(result.authorization_url);
        if(target.protocol!=="https:"||target.hostname!=="accounts.google.com")throw new Error("Google authorization URL ไม่ถูกต้อง");
        window.location.assign(target.href);return;
      }
      if(plugin.connect_action==="github-app-token"){
        await api("/api/integrations/github-app/token",{method:"POST",body:JSON.stringify({})});
        toast("GitHub App installation token พร้อมใช้งานผ่าน Credential Broker");
        await refreshPluginCatalog();return;
      }
    }catch(error){toast("เชื่อมต่อ "+plugin.name+" ไม่สำเร็จ: "+error.message);}
    finally{button.disabled=false;}
  }
  function openSettings(){ $("#token-input").value=""; $("#settings-dialog").showModal(); }
  function setView(name){
    document.querySelectorAll(".view").forEach(v=>v.classList.remove("active"));
    $("#"+name+"-view").classList.add("active");
    document.querySelectorAll(".side-link[data-panel]").forEach(b=>b.classList.toggle("active",b.dataset.panel===name));
    $("#view-label").textContent=name.toUpperCase();
    if(name==="history") loadHistory();
    if(name==="functions") renderFunctions();
    if(name==="connections") refreshPluginCatalog();
  }
  function renderSystemPanel(){
    const status=state.status||{};
    const databaseReady=status.database_ready===true;
    const mode=String(status.mode||"unknown").toUpperCase();
    const mock=String(status.mode||"").toLowerCase()==="mock";
    const core=$("#neural-core");
    core.classList.toggle("core-ready",databaseReady);
    core.classList.toggle("core-mock",mock);
    $("#core-state").textContent=databaseReady?"CORE READY":"CORE OFFLINE";
    $("#core-substate").textContent=mock?"MOCK · NO LIVE INFERENCE":(status.model||"RUNTIME STATUS UNKNOWN").toUpperCase();
    $("#topology-caption").textContent=databaseReady?"RUNTIME LINK VERIFIED":"RUNTIME LINK UNAVAILABLE";
    $("#metric-agents").textContent=String(state.agents.length).padStart(2,"0");
    $("#metric-database").textContent=databaseReady?"READY":"OFFLINE";
    $("#metric-mode").textContent=mode;
    $("#neural-foot").textContent=mock?"โหมด MOCK: ยังไม่มี Live inference provider · โหนดรอบ Core แสดงเฉพาะ Agent ที่ลงทะเบียน":"โหนดรอบ Core แสดงเฉพาะ Agent ที่ลงทะเบียน ไม่ได้ยืนยันว่ากำลังประมวลผล";
    const orbit=$("#agent-orbit");orbit.replaceChildren();
    const count=state.agents.length;
    state.agents.forEach((agent,index)=>{
      const angle=(Math.PI*2*index/Math.max(count,1))-Math.PI/2;
      const radius=count>3?Math.min(154,Math.max(116,window.innerWidth<650?112:142)):Math.min(140,window.innerWidth<650?105:126);
      const node=document.createElement("div");node.className="orbit-agent";
      node.style.left=`calc(50% + ${Math.cos(angle)*radius}px)`;
      node.style.top=`calc(50% + ${Math.sin(angle)*radius}px)`;
      const dot=document.createElement("i");dot.setAttribute("aria-hidden","true");
      const name=document.createElement("span");name.textContent=agent.name;
      const stateLabel=document.createElement("small");stateLabel.textContent="REGISTERED";
      node.append(dot,name,stateLabel);orbit.append(node);
    });
  }
  function renderAgents(){
    const picker=$("#agent-picker"); picker.replaceChildren();
    state.agents.forEach(agent=>{const option=document.createElement("option");option.value=agent.id;option.textContent=agent.name;picker.append(option);});
    $("#send-button").disabled=!state.agents.length;
    renderSystemPanel();
    const suggestions=$("#suggestions");suggestions.replaceChildren();
    state.agents.slice(0,4).forEach((agent,index)=>{
      const button=document.createElement("button");button.className="suggestion";button.type="button";
      const glyph=document.createElement("span");glyph.textContent=["✧","⌕","✎","◎"][index]||"◈";
      const title=document.createElement("b");title.textContent=agent.name;
      const desc=document.createElement("small");desc.textContent=agent.description||"Agent ที่ลงทะเบียนใน CK-NEXUS";
      button.append(glyph,title,desc);
      button.addEventListener("click",()=>{picker.value=agent.id;$("#prompt").value=agent.example||"";$("#prompt").focus();});
      suggestions.append(button);
    });
    if(!state.agents.length){suggestions.innerHTML='<p class="muted">ยังไม่มี Agent ที่เปิดให้ใช้งานผ่าน API นี้</p>';}
  }
  function renderFunctions(){
    const root=$("#function-list");root.replaceChildren();
    if(!state.agents.length){root.textContent="ไม่พบ Agent ที่พร้อมแสดง";return;}
    state.agents.forEach(agent=>{
      const card=document.createElement("article");card.className="function-card";
      const icon=document.createElement("span");icon.className="function-icon";icon.textContent="◈";
      const copy=document.createElement("div");const title=document.createElement("strong");title.textContent=agent.name;
      const desc=document.createElement("small");desc.textContent=agent.description||"ลงทะเบียนใน CK-NEXUS Agent registry";
      copy.append(title,desc);card.append(icon,copy);root.append(card);
    });
  }
  async function searchDiscoveredTools(event){
    event.preventDefault();
    const query=$("#tool-search-query").value.trim();
    const root=$("#tool-search-results");
    const button=$("#tool-search-submit");
    if(query.length<2){toast("กรุณาพิมพ์คำค้นอย่างน้อย 2 ตัวอักษร");return;}
    button.disabled=true;button.textContent="Searching…";
    root.replaceChildren();
    const loading=document.createElement("p");loading.className="muted";loading.textContent="กำลังค้นหา Schema ที่ผ่านการตรวจสอบ…";root.append(loading);
    try{
      const result=await api("/api/tools/search?"+new URLSearchParams({q:query,limit:"30"}));
      root.replaceChildren();
      if(!result.available){const note=document.createElement("p");note.className="muted";note.textContent=result.message||"Connector Fabric ยังไม่พร้อม";root.append(note);return;}
      if(!result.results.length){const note=document.createElement("p");note.className="muted";note.textContent="ไม่พบ Function ที่ตรงกับคำค้นใน Schema ที่ตรวจสอบแล้ว";root.append(note);return;}
      const summary=document.createElement("p");summary.className="tool-search-summary";summary.textContent="พบ "+result.count+" Function · Discovery only · Execution disabled";root.append(summary);
      result.results.forEach(item=>{
        const card=document.createElement("article");card.className="tool-result-card";
        const head=document.createElement("div");head.className="tool-result-head";
        const name=document.createElement("strong");name.textContent=item.name;
        const risk=document.createElement("span");risk.className="tool-risk "+(item.risk==="READ_ONLY"?"read-only":"approval");risk.textContent=item.risk;
        head.append(name,risk);
        const logical=document.createElement("code");logical.textContent=item.logical_name;
        const description=document.createElement("p");description.textContent=item.description||"No description supplied";
        const meta=document.createElement("small");meta.textContent="Connector: "+item.connector_id+" · Match: "+Math.round(item.score*100)+"% · "+item.connector_state;
        const gate=document.createElement("small");gate.className="tool-result-gate";gate.textContent=item.approval_required?"ต้องขออนุมัติตามนโยบายก่อนใช้งาน":"Read-only · ยังต้องผ่าน Core Policy";
        card.append(head,logical,description,meta,gate);root.append(card);
      });
    }catch(error){
      root.replaceChildren();const note=document.createElement("p");note.className="muted";note.textContent=error.status===401?"ต้องตั้งค่า CK-NEXUS Access Token ใน Settings":("ค้นหาไม่สำเร็จ: "+error.message);root.append(note);
    }finally{button.disabled=false;button.textContent="Search functions";}
  }
  async function inspectMcpCandidate(item,card,button){
    let panel=card.querySelector(".mcp-detail-panel");
    if(!panel){panel=document.createElement("div");panel.className="mcp-detail-panel";card.append(panel);}
    button.disabled=true;button.textContent="Inspecting metadata…";
    panel.textContent="กำลังอ่านข้อมูล package และ transport จาก Official MCP Registry…";
    try{
      const params=new URLSearchParams({name:item.name,version:item.version});
      const detail=await api("/api/tools/discovery/mcp-registry/details?"+params);
      panel.replaceChildren();
      const title=document.createElement("strong");title.textContent="Registry metadata · "+detail.registry_status+" · "+detail.version;panel.append(title);
      if(detail.repository_url){const repo=document.createElement("p");repo.textContent="Repository: "+detail.repository_url+(detail.repository_subfolder?" · subfolder: "+detail.repository_subfolder:"");panel.append(repo);}
      if(detail.website_host){const site=document.createElement("p");site.textContent="Website host (unverified): "+detail.website_host;panel.append(site);}
      const packageTitle=document.createElement("p");packageTitle.className="muted";packageTitle.textContent="Packages / transports";panel.append(packageTitle);
      (detail.packages||[]).forEach(pkg=>{
        const line=document.createElement("p");line.textContent=[pkg.registry_type,pkg.identifier,pkg.version,pkg.transport,pkg.runtime_hint].filter(Boolean).join(" · ");panel.append(line);
        (pkg.configuration_hints||[]).forEach(hint=>{const env=document.createElement("small");env.className="mcp-config-hint";env.textContent=hint.name+(hint.required?" · required":"")+(hint.secret?" · secret value required":"");panel.append(env);});
      });
      (detail.remotes||[]).forEach(remote=>{const line=document.createElement("small");line.className="mcp-config-hint";line.textContent="Remote: "+remote.transport+" · host "+remote.host;panel.append(line);});
      const warning=document.createElement("p");warning.className="tool-result-gate";warning.textContent="OBSERVED เท่านั้น · ยังไม่ตรวจ License / Provenance / Security · ไม่ติดตั้งและไม่อนุญาตให้ Execute";panel.append(warning);
    }catch(error){panel.textContent="อ่านรายละเอียดไม่สำเร็จ: "+error.message;}
    finally{button.disabled=false;button.textContent="Inspect metadata";}
  }
  async function searchMcpRegistry(loadMore=false){
    const query=loadMore?state.mcpQuery:$("#tool-search-query").value.trim();
    const root=$("#tool-search-results");
    const button=$("#mcp-registry-search");
    if(query.length<3){toast("MCP Registry ต้องใช้คำค้นอย่างน้อย 3 ตัวอักษร");return;}
    if(!loadMore){state.mcpQuery=query;state.mcpCursor=null;state.mcpCandidates=[];}
    button.disabled=true;button.textContent="Searching registry…";
    if(!loadMore){root.replaceChildren();const loading=document.createElement("p");loading.className="muted";loading.textContent="กำลังค้นหา Official MCP Registry…";root.append(loading);}
    try{
      const params=new URLSearchParams({q:query,limit:"20"});
      if(loadMore&&state.mcpCursor)params.set("cursor",state.mcpCursor);
      const result=await api("/api/tools/discovery/mcp-registry?"+params);
      state.mcpCursor=result.next_cursor||null;
      const combined=loadMore?[...state.mcpCandidates,...result.results]:result.results;
      const unique=new Map(combined.map(item=>[item.name+"@"+item.version,item]));
      state.mcpCandidates=[...unique.values()];
      root.replaceChildren();
      if(!state.mcpCandidates.length){const note=document.createElement("p");note.className="muted";note.textContent="ไม่พบ MCP Server ที่ active และเป็น latest version";root.append(note);return;}
      const summary=document.createElement("p");summary.className="tool-search-summary";summary.textContent="Official MCP Registry · "+state.mcpCandidates.length+" candidates loaded · OBSERVED only";root.append(summary);
      state.mcpCandidates.forEach(item=>{
        const card=document.createElement("article");card.className="tool-result-card";
        const head=document.createElement("div");head.className="tool-result-head";
        const name=document.createElement("strong");name.textContent=item.name;
        const stateLabel=document.createElement("span");stateLabel.className="tool-risk approval";stateLabel.textContent="OBSERVED";
        head.append(name,stateLabel);
        const description=document.createElement("p");description.textContent=item.description||"No description supplied";
        const meta=document.createElement("small");meta.textContent="Version "+item.version+" · Registry status "+item.registry_status;
        const gate=document.createElement("small");gate.className="tool-result-gate";gate.textContent="ยังไม่ติดตั้ง · ยังไม่อนุญาตให้เรียกใช้ · ต้องตรวจสอบ License และ Provenance";
        const inspect=document.createElement("button");inspect.type="button";inspect.className="registry-inspect-button";inspect.textContent="Inspect metadata";inspect.addEventListener("click",()=>inspectMcpCandidate(item,card,inspect));
        card.append(head,description,meta,gate,inspect);root.append(card);
      });
      if(state.mcpCursor){const more=document.createElement("button");more.type="button";more.id="mcp-registry-more";more.className="registry-more-button";more.textContent="Load more MCP servers";more.addEventListener("click",()=>searchMcpRegistry(true));root.append(more);}
    }catch(error){
      root.replaceChildren();const note=document.createElement("p");note.className="muted";note.textContent=error.status===401?"ต้องตั้งค่า CK-NEXUS Access Token ใน Settings":("MCP Registry ค้นหาไม่สำเร็จ: "+error.message);root.append(note);
    }finally{button.disabled=false;button.textContent="Search MCP Registry";}
  }
  function addMessage(role,content,error=false){
    const node=document.createElement("article");node.className="message "+role+(error?" error":"");
    const meta=document.createElement("div");meta.className="message-meta";meta.textContent=role==="user"?"YOU":"NEXUS · CK-NEXUS";
    const body=document.createElement("div");body.textContent=content;node.append(meta,body);$("#conversation").append(node);node.scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"nearest"});
    return node;
  }
  async function sendMessage(event){
    event.preventDefault();if(state.busy)return;
    const prompt=$("#prompt").value.trim(),agentId=$("#agent-picker").value;
    if(!prompt)return;if(!agentId){toast("ยังไม่มี Agent ที่พร้อมใช้งาน");return;}
    addMessage("user",prompt);$("#prompt").value="";state.busy=true;$("#send-button").disabled=true;$("#send-button").textContent="…";
    const waiting=addMessage("assistant","กำลังส่งคำขอไปยัง CK-NEXUS…");
    try{
      const run=await api("/api/runs",{method:"POST",body:JSON.stringify({agent_id:agentId,prompt,audience:"ผู้ใช้",platform:"NEXUS Workspace",tone:"เป็นธรรมชาติ",language:"ไทย",session_id:state.session})});
      waiting.remove();
      addMessage("assistant",run.content||"งานเสร็จแล้ว แต่ API ไม่ได้ส่งเนื้อหาผลลัพธ์กลับมา");
      toast("ได้รับผลลัพธ์จาก CK-NEXUS");
    }catch(error){
      waiting.remove();
      if(error.status===401){addMessage("assistant","ต้องยืนยันสิทธิ์ก่อนใช้งาน กรุณาเปิด Settings และตั้งค่า Access Token ในเครื่องนี้",true);}
      else addMessage("assistant","คำขอไม่สำเร็จ: "+error.message,true);
    }finally{state.busy=false;$("#send-button").disabled=!state.agents.length;$("#send-button").textContent="↑";}
  }
  async function loadHistory(){
    const root=$("#history-list");root.replaceChildren();
    try{
      const runs=await api("/api/runs?"+new URLSearchParams({session_id:state.session,limit:"30"}));
      if(!runs.length){root.innerHTML='<p class="muted">ยังไม่มีประวัติใน session นี้</p>';return;}
      runs.forEach(run=>{
        const button=document.createElement("button");button.type="button";button.className="history-item";
        const copy=document.createElement("span");const title=document.createElement("strong");title.textContent=run.prompt;
        const meta=document.createElement("small");meta.textContent=[run.agent_name,run.platform,run.mode].filter(Boolean).join(" / ");copy.append(title,meta);
        const time=document.createElement("time");time.textContent=run.created_at?new Date(run.created_at).toLocaleString("th-TH"):"";
        button.append(copy,time);button.addEventListener("click",()=>{setView("chat");addMessage("user",run.prompt);addMessage("assistant",run.content||"ไม่มีเนื้อหาผลลัพธ์");});root.append(button);
      });
    }catch(error){root.innerHTML='<p class="muted">โหลดประวัติไม่ได้: '+escapeHtml(error.message)+'</p>';if(error.status===401)toast("ต้องตั้งค่า Access Token");}
  }
  function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
  async function initialize(){
    sessionStorage.setItem(SESSION_KEY,state.session);
    try{
      const status=await api("/api/status");
      state.status=status;
      $("#status-label").textContent=status.database_ready?"Runtime connected":"Database unavailable";
      $("#status-dot").classList.toggle("ok",Boolean(status.database_ready));
      const mockMode=status.mode==="mock";
      $("#runtime-mode").textContent=mockMode?"MOCK AI · DEVELOPMENT":(status.mode||"unknown").toUpperCase()+" RUNTIME";
      $("#runtime-mode").classList.toggle("mock",mockMode);
      $("#model-label").textContent=mockMode?"No live inference provider":(status.model||"model unavailable");
    }catch(error){state.status=null;$("#status-label").textContent="Runtime unreachable";$("#model-label").textContent=error.message;}
    try{const result=await api("/api/agents");state.agents=Array.isArray(result.agents)?result.agents:[];renderAgents();}
    catch(error){state.agents=[];renderAgents();$("#status-label").textContent=error.status===401?"Access required":"Agent registry unavailable";$("#model-label").textContent="Open Settings to configure access";}
  }
  document.querySelectorAll(".side-link[data-panel]").forEach(button=>button.addEventListener("click",()=>setView(button.dataset.panel)));
  $("#new-chat").addEventListener("click",()=>{$("#conversation").replaceChildren();$("#prompt").value="";setView("chat");});
  $("#chat-form").addEventListener("submit",sendMessage);
  $("#prompt").addEventListener("keydown",event=>{if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();$("#chat-form").requestSubmit();}});
  $("#settings-open").addEventListener("click",openSettings);$("#settings-shortcut").addEventListener("click",openSettings);
  $("#connections-shortcut").addEventListener("click",()=>setView("connections"));
  $("#plugins-refresh").addEventListener("click",refreshPluginCatalog);
  $("#tool-search-form").addEventListener("submit",searchDiscoveredTools);
  $("#mcp-registry-search").addEventListener("click",searchMcpRegistry);
  const gmailResult=new URLSearchParams(location.search).get("gmail");
  if(gmailResult==="connected")toast("Google ยืนยันการเชื่อมต่อ Gmail แล้ว");
  else if(gmailResult==="denied")toast("ยกเลิกการอนุญาต Gmail");
  else if(gmailResult==="failed")toast("การเชื่อมต่อ Gmail ไม่สำเร็จ กรุณาลองใหม่");
  if(gmailResult){history.replaceState({},"",location.pathname);setView("connections");}
  $("#save-token").addEventListener("click",()=>{const value=$("#token-input").value.trim();if(!value){toast("กรุณากรอก token ในช่องนี้");return;}sessionStorage.setItem(TOKEN_KEY,value);$("#settings-dialog").close();initialize();toast("บันทึก token ใน session นี้แล้ว");});
  $("#clear-token").addEventListener("click",()=>{sessionStorage.removeItem(TOKEN_KEY);$("#settings-dialog").close();initialize();toast("ล้าง token จาก session แล้ว");});
  $("#settings-dialog").addEventListener("click",event=>{if(event.target.id==="settings-dialog")$("#settings-dialog").close();});
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!reduceMotion && window.matchMedia("(pointer:fine)").matches) {
    let frame = 0;
    document.addEventListener("pointermove", event => {
      if (frame) return;
      frame = requestAnimationFrame(() => {
        document.documentElement.style.setProperty("--pointer-x", event.clientX + "px");
        document.documentElement.style.setProperty("--pointer-y", event.clientY + "px");
        frame = 0;
      });
    }, { passive: true });
  }
  document.querySelectorAll(".suggestion,.side-link,.new-chat,.send-button").forEach(el => {
    el.addEventListener("pointerdown", () => el.classList.add("is-pressed"));
    ["pointerup","pointercancel","pointerleave"].forEach(type =>
      el.addEventListener(type, () => el.classList.remove("is-pressed"))
    );
  });
  $("#music-toggle").addEventListener("click",()=>{
    const body=$("#music-body");body.hidden=!body.hidden;
    const open=!body.hidden;$("#music-toggle").textContent=open?"Close":"Open";
    $("#music-toggle").setAttribute("aria-expanded",String(open));
    $("#music-dock").classList.toggle("expanded",open);
  });
  $("#music-close").addEventListener("click",()=>{
    $("#music-dock").hidden=true;
    $("#music-reopen").hidden=false;
    $("#music-body").hidden=true;
    $("#music-toggle").textContent="Open";
    $("#music-toggle").setAttribute("aria-expanded","false");
    $("#music-dock").classList.remove("expanded");
  });
  $("#music-reopen").addEventListener("click",()=>{
    $("#music-dock").hidden=false;
    $("#music-reopen").hidden=true;
  });

  initialize();
})();