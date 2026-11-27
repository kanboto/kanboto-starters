import type { Component } from 'vue'
import {
  ArrowRight, Bell, BookOpen, Calendar, Camera, ChartColumn, Check, CircleCheck, Clock, Cloud, Code,
  CreditCard, Database, Download, FileText, Filter, Folder, Globe, Heart, House, Image, Inbox, Layers,
  LayoutDashboard, LifeBuoy, List, Lock, LogIn, Mail, MapPin, MessageSquare, Package, Pencil, Phone, Plus,
  Rocket, Search, Settings, ShieldCheck, ShoppingCart, Sparkles, Star, Tag, Trash2, Truck, Upload, User,
  UserPlus, Users, Wrench, Zap,
} from 'lucide-vue-next'

/** The icons a page document may name, by their lucide name. An allowlist: importing every icon would ship
 * them all. Add the one a project needs here. */
const ICONS: Record<string, Component> = {
  'arrow-right': ArrowRight,
  'bell': Bell,
  'book-open': BookOpen,
  'calendar': Calendar,
  'camera': Camera,
  'chart-column': ChartColumn,
  'check': Check,
  'circle-check': CircleCheck,
  'clock': Clock,
  'cloud': Cloud,
  'code': Code,
  'credit-card': CreditCard,
  'database': Database,
  'download': Download,
  'file-text': FileText,
  'filter': Filter,
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
  'log-in': LogIn,
  'mail': Mail,
  'map-pin': MapPin,
  'message-square': MessageSquare,
  'package': Package,
  'pencil': Pencil,
  'phone': Phone,
  'plus': Plus,
  'rocket': Rocket,
  'search': Search,
  'settings': Settings,
  'shield-check': ShieldCheck,
  'shopping-cart': ShoppingCart,
  'sparkles': Sparkles,
  'star': Star,
  'tag': Tag,
  'trash': Trash2,
  'truck': Truck,
  'upload': Upload,
  'user': User,
  'user-plus': UserPlus,
  'users': Users,
  'wrench': Wrench,
  'zap': Zap,
}

/** The icon of that name, or a neutral one when the name is missing or unknown. */
export function icon(name: string | undefined): Component {
  return (name && ICONS[name]) || Sparkles
}
