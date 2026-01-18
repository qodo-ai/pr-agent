// Test file to trigger analyzers
import { MongoClient } from 'mongodb';
import { Client } from '@elastic/elasticsearch';

// MONGO001: Missing index hint
async function queryUsers(db: any) {
  const result = await db.collection('users').find({
    $or: [{ email: 'test@example.com' }, { username: 'testuser' }],
    status: 'active'
  }).toArray();
  return result;
}

// MONGO002: $regex without anchor
async function searchByName(db: any, pattern: string) {
  return await db.collection('users').find({
    name: { $regex: pattern }
  }).toArray();
}

// ES001: Leading wildcard
async function searchElastic(client: Client) {
  const result = await client.search({
    index: 'my-index',
    body: {
      query: {
        wildcard: {
          name: '*smith'
        }
      }
    }
  });
  return result;
}

// PUBSUB001: Missing @PubSubAsyncAcknowledge
@PubSubTopic('USER_TOPIC')
@PubSubEvent('USER_CREATED_EVENT')
public onUserCreated(@PubSubPayload() message: any) {
  console.log('User created:', message);
}

// TS001: let instead of const
function calculateTotal() {
  let count = 0;
  for (let i = 0; i < 10; i++) {
    count += i;
  }
  return count;
}
