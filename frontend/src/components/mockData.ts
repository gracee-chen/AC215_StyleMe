export interface ClothingItem {
  id: string;
  image: string;
  category: string;
  color: string;
  dateAdded: Date;
}

export const initialItems: ClothingItem[] = [
  {
    id: '1',
    image: "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?auto=format&fit=crop&q=80&w=500",
    category: 'Tops',
    color: 'White',
    dateAdded: new Date(Date.now() - 100000000)
  },
  {
    id: '2',
    image: "https://images.unsplash.com/photo-1542272617-08f08375816c?auto=format&fit=crop&q=80&w=500",
    category: 'Bottoms',
    color: 'Blue',
    dateAdded: new Date(Date.now() - 200000000)
  },
  {
    id: '3',
    image: "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&q=80&w=500",
    category: 'Tops',
    color: 'Grey',
    dateAdded: new Date(Date.now() - 300000000)
  },
  {
    id: '4',
    image: "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?auto=format&fit=crop&q=80&w=500",
    category: 'Bottoms',
    color: 'Brown',
    dateAdded: new Date(Date.now() - 400000000)
  },
  {
    id: '5',
    image: "https://images.unsplash.com/photo-1551488852-0801464bdd52?auto=format&fit=crop&q=80&w=500",
    category: 'Outerwear',
    color: 'Black',
    dateAdded: new Date(Date.now() - 500000000)
  }
];
