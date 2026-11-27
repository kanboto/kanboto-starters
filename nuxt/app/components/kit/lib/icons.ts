import type { Component } from 'vue'
import {
  Bell, BookOpen, Calendar, ChartColumn, Check, CircleCheck, Clock, Cloud, Code, CreditCard, Database, FileText,
  Folder, Globe, Heart, House, Image, Inbox, Layers, LayoutDashboard, LifeBuoy, List, Lock, Mail, MapPin,
  MessageSquare, Package, Phone, Rocket, Search, Settings, ShieldCheck, ShoppingCart, Sparkles, Star, Tag,
  Truck, User, Users, Wrench, Zap,
} from 'lucide-vue-next'

/** The icons a page document may name, by their lucide name. An allowlist: importing every icon would ship
 * them all. Add the one a project needs here. */
const ICONS: Record<string, Component> = {
  'bell': Bell,
  'book-open': BookOpen,
  'calendar': Calendar,
  'chart-column': ChartColumn,
  'check': Check,
  'circle-check': CircleCheck,
  'clock': Clock,
  'cloud': Cloud,
  'code': Code,
  'credit-card': CreditCard,
  'database': Database,
  'file-text': FileText,
  'folder': Folder,
  'globe': Globe,
  'heart': Heart,
  'house': House,
  'image': Image,
  'inbox': Inbox,
  'layers': Layers,
  'layout-dashboard': LayoutDashboard,
  'life-buoy': LifeBuoy,
  'list': List,
  'lock': Lock,
  'mail': Mail,
  'map-pin': MapPin,
  'message-square': MessageSquare,
  'package': Package,
  'phone': Phone,
  'rocket': Rocket,
  'search': Search,
  'settings': Settings,
  'shield-check': ShieldCheck,
  'shopping-cart': ShoppingCart,
  'sparkles': Sparkles,
  'star': Star,
  'tag': Tag,
  'truck': Truck,
  'user': User,
  'users': Users,
  'wrench': Wrench,
  'zap': Zap,
}

/** The icon of that name, or a neutral one when the name is missing or unknown. */
export function icon(name: string | undefined): Component {
  return (name && ICONS[name]) || Sparkles
}
