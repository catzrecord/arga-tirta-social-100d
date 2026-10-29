import fs from 'node:fs/promises';
import crypto from 'node:crypto';

async function token(file, aad, fallback) {
  let stored;
  try {stored=JSON.parse(await fs.readFile(file));}catch(error){if(error.code==='ENOENT')return fallback;throw error;}
  const key=Buffer.from(process.env.META_TOKEN_ENCRYPTION_KEY||'','base64');
  if(key.length!==32)throw Error('Encrypted credential key unavailable');
  const decipher=crypto.createDecipheriv('aes-256-gcm',key,Buffer.from(stored.iv,'base64'));
  decipher.setAAD(Buffer.from(aad));decipher.setAuthTag(Buffer.from(stored.tag,'base64'));
  return JSON.parse(Buffer.concat([decipher.update(Buffer.from(stored.ciphertext,'base64')),decipher.final()]).toString()).access_token;
}

const definitions=[
  {platform:'instagram',url:`https://graph.instagram.com/v25.0/${process.env.INSTAGRAM_USER_ID}?fields=id,username,account_type`,
    expected_id:process.env.INSTAGRAM_USER_ID,expected_name:'cv.argatirta',file:'.state/meta-token.enc',aad:'arga-tirta-meta-token:v1',fallback:process.env.META_ACCESS_TOKEN},
  {platform:'threads',url:'https://graph.threads.net/me?fields=id,username',expected_name:'cv.argatirta',
    file:'.state/threads-token.enc',aad:'arga-tirta-threads-token:v1',fallback:process.env.THREADS_ACCESS_TOKEN},
  {platform:'facebook',url:'https://graph.facebook.com/v25.0/me?fields=id,name,link',expected_id:'61596094737525',
    expected_name:'Selamet Iskandar',fallback:process.env.FACEBOOK_PAGE_ACCESS_TOKEN}
];
const accounts=[];
for(const entry of definitions) {
  const out={platform:entry.platform,expected_name:entry.expected_name};
  try {
    const access=entry.file?await token(entry.file,entry.aad,entry.fallback):entry.fallback;
    if(!access){accounts.push({...out,status:'credential_missing'});continue;}
    const response=await fetch(entry.url,{headers:{Authorization:`Bearer ${access}`},signal:AbortSignal.timeout(25000)});
    const data=await response.json();
    if(!response.ok || data.error) {
      accounts.push({...out,status:'authorization_failed',code:data.error?.code||response.status,
        expired:/expir/i.test(data.error?.message||'')});continue;
    }
    const name=data.username||data.name;
    const matches=name?.toLowerCase()===entry.expected_name.toLowerCase() && (!entry.expected_id || String(data.id)===entry.expected_id);
    accounts.push({...out,status:matches?'identity_verified':'identity_mismatch',actual_name:name,id:data.id});
  }catch(error) {accounts.push({...out,status:'verification_failed',reason:error.name==='TimeoutError'?'timeout':'credential_or_network_check_failed'});}
}
const report={checked_at:new Date().toISOString(),read_only:true,publish_requests_made:0,accounts};
await fs.writeFile('annual-live-connections.json',JSON.stringify(report,null,2)+'\n');
console.log('ARGA_CONNECTION_REPORT '+JSON.stringify(report));
