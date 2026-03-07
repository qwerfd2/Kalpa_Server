# Kalpa_Server

## Intro:

A local server for mobile rhythm game `Kalpa`, implemented using `starlette`.

Reminder, this repo contains no copyrighted content (keys, assets, etc.)

PC server is made but not released for now (If you understand this codebase then coding it on your own should be trivial anyways, it's basically the same stuff but much simpler)

Also, disclaimer, AI assistance was used in this project. Without it, it would certainly be impossible to accomplish the goals set out. Don't be an ostrich, and certainly don't put your head in the sand.

## Features:

:x: : Not supported  
:warning: : Possible issues / may differ from official  
:construction: : In construction

### Features that are supported (Mobile)

- Database foundation

- User registration and login flow

- Full unlock (song, character, icon, note, etc.) capability

- Song play gameloop

- Customization of character, skin, icon, playnote, background, etc.

- Public profile

- Daily mission

- Performer level

- Friends

- Mailbox

- Stage Mode

- Player rating (b50) :warning:

- Subscription

- Gacha

- Noah

- Labs

- Darkmoon

- Achievement

- Character serverside skills

- Multiplay

- Local, email, discord auth

### Features that cannot be supported due to their removal (mobile)

- Dark Area

- Battle Pass

- Team competitive event (?)

### Features that are not supported (mobile)

- None 

### Known bugs/quirks

- Some unlock logics are not supported as of now, resulting in the necessity of the unlock_all script/function.

- For noah lab missions, the increment trigger is placed at the time of achievement completion, not when the reward is redeemed. This is a feature, not a bug.

- Unlike the official server, currency deduction happens at the beginning of play (rather than at the end), with only one exception on the top of my mind (Lab journal type mission). Furthermore, rewards can only be claimed once during the `end` api call (client will repeat the call if network issue occurs, which, on the official server, will issue the reward again...)

- With multiplay: Socket IO will attempt to upgrade the connection, so a direct network path must be present for multiplay. That means no network layer proxies like charles. If you are using a per-app proxy setup, that would mess with the normal API features. You can either use frida, or edit all the urls in global-metadata to point directly to your server. Note that unity will enforce https, so a custom certificate that is trusted by the device's verification mechanism need to be used (sign it with charles cert, or use a device-level proxy app like reqable on the background to make the client trust the chain)

## Setup:

### Server setup:

This server requires quite some setup, so you should follow along carefully. I will not provide assistance regarding setup in the issues section. Any tools mentioned will have their respective readme docs in their own folder. Unless there is an issue with the manual, my only advice would be RTFM.

1. Clone this repo (or download zip) using Git or the big green button.

2. Put the code in a folder. Make sure you have `python >3.10`, and `pip` installed.

3. Run `pip install requirements.txt` to install all the dependencies.

4. Generate a RSA key pair (used for song play) using the `tools/cryptGen`, and move the generated `xml` and `pem` to `api/config`.

5. Capture the packet of the official server's `/api/initialinfo` API endpoint. Copy the `data` string and store it in `b64.txt`. We will use it later. To capture packet, you can use charles, reqable, forge request, or other arcane method, as long as you can get it no one cares how.

6. Copy the `b64.txt` to `tools/parser` and `tools/downloader`.

7. In `parser`, run `python parser2.py`. This will generate three database files `manifest.db`, `player.db`, and `diff_manifest.db`. Copy the first two to the server root directory. 

8. A `config` folder will also be generated. Copy the folder and merge it to server root directory `api/config`.

In future updates, repeat step 5-8, but only copy `manifest.db` and the folder files. The purpose of `diff_manifest.db` is found in the parser's doc.

9. (Optional) In `downloader`, run `python downloader.py`. This will download all the asset files (audio, images, maps, etc.), should you want to serve the assets locally.

10. (Optional) After download, simply copy all the folders under `downloader` to server root directory `files`.

11. Open `config.py`. Edit the host and port information appropriately. Set the `PACK_ICON_ATLAS_FILENAME` and `LOCALIZATION_ENTRY_FILENAME` to the ones printed by the `parser`. If you wish to use discord or email auth, configure the discord bot/api or SMTP credentials.

12. Start the API server by running `python 12001.py`. Start the multiplay server by running `python 12002.py`.

### Client setup:

All the url strings are in global metadata. Go wild. You should know what to do here. I will not be able to provide the url to replace or otherwise elaborate on the subject.

You can also skip this process and instead go the MITM route. This process is well documented in my other server repos, so if you need help on that, go read this: [GC server](https://github.com/qwerfd2/Groove_Coaster_2_Server/blob/main/README.md#instruction-for-use-for-official-client)

I will not be able to provide help or otherwise elaborate on the subject.

## Note:

### Rating implementation:

B50, no recent.

Formula derived from old PC version (prior to the big update, new update/pc server uses a different formula)

### Other things

A couple interesting things to look into:

The manifest contains unused songs and charts

PC charts works in mobile too

A set of manifest diff that allows organic progression???