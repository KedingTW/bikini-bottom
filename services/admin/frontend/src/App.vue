<template>
  <AppLayout v-if="!isLogin">
    <router-view />
  </AppLayout>
  <router-view v-else />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './components/AppLayout.vue'

const route = useRoute()
const isLogin = computed(() => route.name === 'login')
</script>
