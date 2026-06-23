<template>
  <div class="relative">
    <button @click="open = !open" type="button" class="flex items-center gap-2 bg-ocean-800 border border-white/15 rounded px-3 py-2 text-sm hover:border-white/30 w-full text-left">
      <span class="text-xl">{{ modelValue }}</span>
      <span class="text-xs text-white/40 ml-auto">▾</span>
    </button>
    <div v-if="open" class="absolute bottom-full left-0 mb-1 z-50 bg-ocean-700 border border-white/20 rounded-lg shadow-xl w-72 max-w-[calc(100vw-2rem)] max-h-[320px] flex flex-col">
      <input v-model="search" placeholder="搜尋或自行輸入 emoji..." class="w-full bg-ocean-800 border-b border-white/15 rounded-t-lg px-3 py-2 text-sm text-white focus:outline-none" @keydown.enter="selectCustom">
      <div class="flex gap-1 px-2 py-1.5 border-b border-white/10 overflow-x-auto no-scrollbar">
        <button v-for="g in groups" :key="g.name" @click="activeGroup = g.name"
          class="text-lg px-1.5 py-0.5 rounded shrink-0" :class="activeGroup === g.name ? 'bg-cyan-600/30' : 'hover:bg-white/10'" :title="g.name">{{ g.icon }}</button>
      </div>
      <div class="flex-1 overflow-y-auto p-2">
        <div class="grid grid-cols-8 gap-0.5">
          <button v-for="e in filteredEmojis" :key="e" @click="select(e)" type="button" class="text-xl p-1.5 rounded hover:bg-white/10 text-center" :title="shortcodes[e] || ''">{{ e }}</button>
        </div>
        <div v-if="!filteredEmojis.length" class="text-center text-sm text-white/40 py-4">無結果</div>
      </div>
    </div>
  </div>
  <div v-if="open" class="fixed inset-0 z-40" @click="open = false"></div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({ modelValue: { type: String, default: '😀' } })
const emit = defineEmits(['update:modelValue'])

const open = ref(false)
const search = ref('')
const activeGroup = ref('比奇堡')

const groups = [
  { name: '比奇堡', icon: '🏝️', emojis: ['🐌','🧽','⭐','🐡','🦑','🐿️','🦞','🐋','🐚','🔥','👀','🤔','⚡','🆗','😱','👨‍💻','📋','🪨','🍔','🏝️','🌊','🎣','⚓','🪸','🐠','🦀','🐙','🫧'] },
  { name: '表情', icon: '😀', emojis: ['😀','😂','🤣','😅','😊','😎','🥳','😢','😡','🤯','🫠','😱','🥹','😤','🫡','🤝','👋','✋','👍','👎','👏','🙏','💪','🫶','🤌','✌️','🤞','🖐️','🙌','🤷','🤦','💀','🥺','😏','🙄','😴','🤗','🫣','🤫','🫢','😶','🤥','😬','🥱','😇','🤓','🧐','😈','👻','💩'] },
  { name: '符號', icon: '✅', emojis: ['✅','❌','⚠️','❓','❗','💡','🔔','📌','📎','🔗','🏷️','✏️','📝','📋','🗂️','📂','📁','📄','📊','📈','📉','🔒','🔑','🛡️','⭕','❎','☑️','✔️','🔄','↩️','↪️','⏩','⏪','▶️','⏸️','⏹️','🔇','🔊','📣','📢','🚨','🆕','🆗','🆘','🈲','🈳','💠','♻️','✳️','❇️','🔰','⚜️'] },
  { name: '工具', icon: '🔧', emojis: ['🔧','🛠️','⚙️','🔩','🔨','💻','🖥️','⌨️','📱','🖨️','💾','📀','🔌','🔋','📡','🛜','🤖','🧠','💡','🔬','🧪','📐','📏','✂️','🗑️','📦','🚀','🎯'] },
  { name: '時間', icon: '⏰', emojis: ['⏰','⏱️','⏳','🕐','🕑','🕒','🕓','🕔','🕕','🕖','🕗','🕘','🕙','🕚','🕛','📅','🗓️','📆','🌅','🌇','🌃','🌙','☀️','⭐','🌟','💫','✨','🎆'] },
  { name: '動物', icon: '🐱', emojis: ['🐱','🐶','🐭','🐹','🐰','🦊','🐻','🐼','🐨','🐯','🦁','🐮','🐷','🐸','🐵','🐔','🐧','🐦','🦆','🦅','🐝','🐛','🦋','🐌','🐙','🦑','🐠','🐳'] },
  { name: '食物', icon: '🍔', emojis: ['🍔','🍟','🌮','🍕','🍣','🍜','🍝','🍛','🍲','🍱','🍙','🍘','🍡','🍧','🍰','🎂','🍪','☕','🍵','🧋','🥤','🍺','🍷','🧃','🍎','🍊','🍋','🍉'] },
  { name: '其他', icon: '🎨', emojis: ['🎨','🎭','🎪','🎠','🎡','🎢','🏆','🥇','🥈','🥉','🎖️','🏅','🎗️','🎫','🎟️','🎪','♠️','♥️','♦️','♣️','🃏','🀄','🎲','🎮','🕹️','🎯','🎳','🎰'] },
]

const shortcodes = {
  '😀':':grinning:','😂':':joy:','🤣':':rofl:','😅':':sweat_smile:','😊':':blush:','😎':':sunglasses:','🥳':':partying_face:','😢':':cry:','😡':':rage:','🤯':':exploding_head:','🫠':':melting_face:','😱':':scream:','🥹':':holding_back_tears:','😤':':triumph:','🫡':':saluting_face:','🤝':':handshake:','👋':':wave:','✋':':raised_hand:','👍':':thumbsup:','👎':':thumbsdown:','👏':':clap:','🙏':':pray:','💪':':muscle:','🫶':':heart_hands:','🤌':':pinched_fingers:','✌️':':v:','🤞':':crossed_fingers:','🖐️':':hand_splayed:','🙌':':raised_hands:','🤷':':shrug:','🤦':':facepalm:','💀':':skull:','🥺':':pleading_face:','😏':':smirk:','🙄':':rolling_eyes:','😴':':sleeping:','🤗':':hugging:','🫣':':peeking:','🤫':':shushing_face:','🫢':':face_with_open_eyes_and_hand_over_mouth:','😶':':no_mouth:','🤥':':lying_face:','😬':':grimacing:','🥱':':yawning_face:','😇':':innocent:','🤓':':nerd:','🧐':':monocle_face:','😈':':smiling_imp:','👻':':ghost:','💩':':poop:',
  '✅':':white_check_mark:','❌':':x:','⚠️':':warning:','❓':':question:','❗':':exclamation:','💡':':bulb:','🔔':':bell:','📌':':pushpin:','📎':':paperclip:','🔗':':link:','🏷️':':label:','✏️':':pencil2:','📝':':memo:','📋':':clipboard:','🗂️':':card_index_dividers:','📂':':open_file_folder:','📁':':file_folder:','📄':':page_facing_up:','📊':':bar_chart:','📈':':chart_with_upwards_trend:','📉':':chart_with_downwards_trend:','🔒':':lock:','🔑':':key:','🛡️':':shield:','⭕':':o:','❎':':negative_squared_cross_mark:','☑️':':ballot_box_with_check:','✔️':':heavy_check_mark:','🔄':':arrows_counterclockwise:','↩️':':leftwards_arrow_with_hook:','↪️':':arrow_right_hook:','⏩':':fast_forward:','⏪':':rewind:','▶️':':arrow_forward:','⏸️':':pause_button:','⏹️':':stop_button:','🔇':':mute:','🔊':':loud_sound:','📣':':mega:','📢':':loudspeaker:','🚨':':rotating_light:','🆕':':new:','🆗':':ok:','🆘':':sos:','💠':':diamond_shape_with_a_dot_inside:','♻️':':recycle:','✳️':':eight_spoked_asterisk:','❇️':':sparkle:','🔰':':beginner:','⚜️':':fleur_de_lis:',
  '🔧':':wrench:','🛠️':':hammer_and_wrench:','⚙️':':gear:','🔩':':nut_and_bolt:','🔨':':hammer:','💻':':computer:','🖥️':':desktop:','⌨️':':keyboard:','📱':':iphone:','🖨️':':printer:','💾':':floppy_disk:','📀':':dvd:','🔌':':electric_plug:','🔋':':battery:','📡':':satellite:','🛜':':wireless:','🤖':':robot:','🧠':':brain:','🔬':':microscope:','🧪':':test_tube:','📐':':triangular_ruler:','📏':':straight_ruler:','✂️':':scissors:','🗑️':':wastebasket:','📦':':package:','🚀':':rocket:','🎯':':dart:',
  '⏰':':alarm_clock:','⏱️':':stopwatch:','⏳':':hourglass_flowing_sand:','📅':':date:','🗓️':':spiral_calendar:','🌅':':sunrise:','🌙':':crescent_moon:','☀️':':sunny:','⭐':':star:','🌟':':star2:','💫':':dizzy:','✨':':sparkles:',
  '🐌':':snail:','🧽':':sponge:','⭐':':star:','🐡':':blowfish:','🦑':':squid:','🐿️':':chipmunk:','🦞':':lobster:','🐋':':whale2:','🐚':':shell:','🔥':':fire:','👀':':eyes:','🤔':':thinking:','⚡':':zap:','👨‍💻':':technologist:','🪨':':rock:','🍔':':hamburger:','🏝️':':island:','🌊':':ocean:','🎣':':fishing_pole:','⚓':':anchor:','🐠':':tropical_fish:','🦀':':crab:','🐙':':octopus:','🫧':':bubbles:',
  '❤️':':heart:','🎉':':tada:','🏆':':trophy:','🥇':':first_place:','🎨':':art:','🎮':':video_game:','🎬':':clapper:','📸':':camera_with_flash:','☕':':coffee:','🍟':':fries:','🌮':':taco:','🍕':':pizza:',
}

const filteredEmojis = computed(() => {
  if (search.value) {
    const q = search.value.toLowerCase()
    const all = groups.flatMap(grp => grp.emojis)
    return all.filter(e => e.includes(search.value) || (shortcodes[e] && shortcodes[e].toLowerCase().includes(q)))
  }
  const found = groups.find(grp => grp.name === activeGroup.value)
  return found ? found.emojis : []
})

function select(e) { emit('update:modelValue', e); open.value = false; search.value = '' }
function selectCustom() { if (search.value.trim()) { emit('update:modelValue', search.value.trim()); open.value = false; search.value = '' } }
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
