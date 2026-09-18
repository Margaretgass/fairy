# Executable code reference

Use IMPLEMENTATION.md for architecture mapping. These are the exact reference evaluators included in this package. Browser code is tested; Swift reference is not compiled here. UI source is in prototype/app.js, bloom-ui.js, final.css and the other files listed in IMPLEMENTATION.md. Native views should bind to existing stores, not start new timer instances.


## Charm milestone engine

Source: prototype/charm-engine.js

```javascript
/* Pure reference evaluator. No currency. Catalog order is display order, not a gate. */
(function(root){'use strict';
const rows=[
['star','First Spark','Star','tasks',1],['matcha','A Little Momentum','Matcha','tasks',5],['potion','Something Magical','Potion','quests',1],['lantern','Welcome Home','Lantern','days',3],['daisy','In Bloom','Daisy','flowers',1],['coffee','Finding Your Rhythm','Coffee','tasks',25],['spellbook','Next Chapter','Spellbook','quests',5],['key','A Familiar Place','Cottage Key','days',10],['basket','Little Garden','Flower Basket','flowers',5],['moon_potion','Moonlit Magic','Moon Potion','tasks',50],['book_stack','Keeper of Stories','Enchanted Book Stack','quests',15],['cottage','Right at Home','Glowing Cottage','days',30],['watering_can','Garden Keeper','Crystal Watering Can','flowers',15],['crystal_star','Quietly Powerful','Crystal Star','tasks',100],['compass','Forest Explorer','Enchanted Compass','quests',30],['teacup','A Season of Magic','Celestial Teacup','days',90],['terrarium','Flourishing','Moonflower Terrarium','flowers',30],['crown','Every Little Step','Golden Star Crown','tasks',250]];
const catalog=rows.map(([id,name,object,metric,threshold],art)=>({id,name,object,metric,threshold,art}));
function fresh(){return {version:1,tasks:[],quests:[],flowers:[],days:[],unlocked:[],pending:[]};}
function evaluate(s,now){for(const c of catalog){if(s[c.metric].length>=c.threshold&&!s.unlocked.some(x=>x.id===c.id)){s.unlocked.push({id:c.id,earnedAt:now,seen:false});s.pending.push(c.id);}}return s;}
function record(state,event,now){const s=structuredClone(state);const allowed=['task','quest','flower','capture','chat','focus'];if(!allowed.includes(event.type))return s;const field={task:'tasks',quest:'quests',flower:'flowers'}[event.type];if(field){if(!event.id)return s;if(!s[field].includes(event.id))s[field].push(event.id);}if(event.day&&!s.days.includes(event.day))s.days.push(event.day);return evaluate(s,now);}
function acknowledge(s,ids){s=structuredClone(s);s.pending=s.pending.filter(id=>!ids.includes(id));return s;}
function seen(s,id){s=structuredClone(s);const x=s.unlocked.find(x=>x.id===id);if(x)x.seen=true;return s;}
function requirement(c){return c.metric==='days'?`Use Fairy on ${c.threshold} different days`:c.metric==='tasks'?`Complete ${c.threshold===1?'your first task':c.threshold+' tasks'}`:c.metric==='quests'?`Finish ${c.threshold===1?'your first quest':c.threshold+' quests'}`:`Grow ${c.threshold===1?'your first flower':c.threshold+' flowers'}`;}
const api={catalog,fresh,record,evaluate,acknowledge,seen,requirement};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Charms=api;
})(globalThis);

```


## Flower timer engine

Source: prototype/bloom-engine.js

```javascript
/* Dependency-free reference domain engine. Time in integer milliseconds. */
(function(root){
'use strict';
const MIN=60000,BLOCK=25*MIN,BREAK=5*MIN,TARGET=4*BLOCK;
const species=['Daisy','Lavender','Rose','Sunflower','Bluebell'];
function create(id,pick,now,collection=[]){return {version:1,plant:{id,species:species[Math.min(4,Math.max(0,Math.floor(pick*5)))],focusMs:0,plantedAt:now},phase:'ready',remainingMs:BLOCK,anchorMs:now,collection:[...collection]};}
function stage(s){let m=s.plant.focusMs/MIN;return m>=100?'Bloomed':m>=75?'Bud':m>=50?'Growing tall':m>=25?'Leaves':m>=10?'Sprout':'Seed';}
function tick(s,now){s=structuredClone(s);if(!['focus','break'].includes(s.phase))return s;let elapsed=Math.max(0,now-s.anchorMs);s.anchorMs=Math.max(now,s.anchorMs);let used=Math.min(elapsed,s.remainingMs);s.remainingMs-=used;
if(s.phase==='focus'){s.plant.focusMs=Math.min(TARGET,s.plant.focusMs+used);if(s.remainingMs===0){if(s.plant.focusMs===TARGET){s.phase='bloomed';if(!s.collection.some(x=>x.id===s.plant.id))s.collection.push({...s.plant,bloomedAt:now});}else if(s.plant.focusMs%BLOCK===0){s.phase='break';s.remainingMs=BREAK;}else{s.phase='pausedFocus';}}}
else if(s.remainingMs===0){s.phase='ready';s.remainingMs=BLOCK;}
return s;}
function start(s,now,minutes=25){s=tick(s,now);if(s.phase==='pausedBreak'){s.phase='break';s.anchorMs=now;return s;}if(!['ready','pausedFocus'].includes(s.phase))return s;if(!Number.isFinite(minutes)||minutes<=0)return s;s.phase='focus';s.remainingMs=Math.min(Math.round(minutes*MIN),BLOCK-s.plant.focusMs%BLOCK);s.anchorMs=now;return s;}
function pause(s,now){s=tick(s,now);if(s.phase==='focus')s.phase='pausedFocus';else if(s.phase==='break')s.phase='pausedBreak';return s;}
function resume(s,now){return s.phase==='pausedFocus'?start(s,now,s.remainingMs/MIN||25):start(s,now);}
function next(s,id,pick,now){return s.phase==='bloomed'?create(id,pick,now,s.collection):s;}
const api={MIN,BLOCK,BREAK,TARGET,species,create,stage,tick,start,pause,resume,next};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Bloom=api;
})(globalThis);

```


## Swift charm evaluator

Source: swift/CharmEvaluator.swift

```swift
// Pure Swift reference. Not compiled in this environment; integrate/test in the existing target.
// Decode specs/charm-catalog.json as [CharmDefinition]. Persist all changes in your repository transaction.
import Foundation

struct CharmDefinition: Codable, Identifiable {
    let id: String
    let name: String
    let object: String
    let metric: String
    let threshold: Int
    let art: Int
}
struct CharmUnlock: Codable, Identifiable {
    let id: String
    let earnedAt: Date
    var seen: Bool = false
}
struct CharmProgress: Codable {
    var tasks: Set<String> = []
    var quests: Set<String> = []
    var flowers: Set<String> = []
    var days: Set<String> = []
    var unlocked: [CharmUnlock] = []
    var pending: [String] = []
    func count(_ metric: String) -> Int {
        switch metric {
        case "tasks": return tasks.count
        case "quests": return quests.count
        case "flowers": return flowers.count
        case "days": return days.count
        default: return 0
        }
    }
}
enum CharmEvent {
    case taskCompleted(id: String)
    case questCompleted(id: String)
    case flowerCompleted(plantID: String)
    case thoughtSaved, messageSent, focusStarted
}
enum CharmEvaluator {
    static func apply(_ event: CharmEvent, dayKey: String?, now: Date,
                      catalog: [CharmDefinition], to previous: CharmProgress) -> CharmProgress {
        var state = previous
        switch event {
        case .taskCompleted(let id):
            guard !id.isEmpty else { return state }; state.tasks.insert(id)
        case .questCompleted(let id):
            guard !id.isEmpty else { return state }; state.quests.insert(id)
        case .flowerCompleted(let id):
            guard !id.isEmpty else { return state }; state.flowers.insert(id)
        case .thoughtSaved, .messageSent, .focusStarted: break
        }
        // Caller supplies nil for passive flower recovery; never count launch as activity.
        if let day = dayKey { state.days.insert(day) }
        for charm in catalog where state.count(charm.metric) >= charm.threshold {
            guard !state.unlocked.contains(where: { $0.id == charm.id }) else { continue }
            state.unlocked.append(CharmUnlock(id: charm.id, earnedAt: now))
            state.pending.append(charm.id)
        }
        return state
    }
    static func acknowledge(_ ids: Set<String>, in state: inout CharmProgress) {
        state.pending.removeAll { ids.contains($0) }
    }
    static func markSeen(_ id: String, in state: inout CharmProgress) {
        if let index = state.unlocked.firstIndex(where: { $0.id == id }) {
            state.unlocked[index].seen = true
        }
    }
}
// Count only validated committed domain actions. This pure function is not a persistence,
// concurrency, authentication or server-authority layer. Use existing transaction boundaries.

```
