require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
    console.error("Missing Supabase credentials in .env");
    process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function wipeIsbank() {
    console.log("Fetching İş Bankası cards...");

    // 1. Get Bank ID
    const { data: bankData, error: bankErr } = await supabase
        .from('MasterBank')
        .select('id')
        .ilike('name', '%İş Bankası%');

    if (bankErr) {
        console.error("Bank Error:", bankErr);
        return;
    }

    if (!bankData || bankData.length === 0) {
        console.log("İş Bankası not found.");
        return;
    }

    const bankIds = bankData.map(b => b.id);

    // 2. Get Card IDs
    const { data: cardData, error: cardErr } = await supabase
        .from('Card')
        .select('id')
        .in('bankId', bankIds);

    if (cardErr) {
        console.error("Card Error:", cardErr);
        return;
    }

    if (!cardData || cardData.length === 0) {
        console.log("No cards found for İş Bankası.");
        return;
    }

    const cardIds = cardData.map(c => c.id);
    console.log(`Found ${cardIds.length} cards. Deleting campaigns...`);

    // 3. Delete Campaigns
    const { data: deleted, error: delErr } = await supabase
        .from('Campaign')
        .delete()
        .in('cardId', cardIds)
        .select('id');

    if (delErr) {
        console.error("Delete Error:", delErr);
        return;
    }

    console.log(`✅ Deleted ${deleted.length} campaigns for Maximum/Maximiles.`);
}

wipeIsbank();
